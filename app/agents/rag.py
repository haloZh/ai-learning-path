"""RAG 资源检索:bge-m3 编码 + Chroma 向量库,支持按 concept_code 过滤。

设计:
- 单例 RagAdapter,模型与 collection 懒加载;模型未下载时调用方会拿到 RagUnavailable
- bootstrap_index(db) 把 resources 表全量(或增量)写入 Chroma,返回写入数
- retrieve(concept_code, query, k=5) 返回元数据列表,索引为空或失败时返回 []

性能:
- 首次加载 bge-m3 (~2GB) 需 5-15s,且默认会查 huggingface hub 拿元数据,
  联网慢时整体会到 30-50s。这里强制 HF_HUB_OFFLINE=1 走纯本地缓存,
  并在 startup 时由 main.lifespan 预热,运行期请求不再触发加载。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

# 强制 hf 离线,只用本地缓存,避免每次启动几十次 HEAD 元数据请求
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

logger = logging.getLogger(__name__)

_MODEL_NAME = "BAAI/bge-m3"
_COLLECTION_NAME = "resources"
_PERSIST_DIR = Path(os.getenv("CHROMA_DIR", "./data/chroma"))


class RagUnavailable(Exception):
    """RAG 不可用(模型未下载 / chromadb 未安装),caller 应降级。"""


class RagAdapter:
    def __init__(self) -> None:
        self._model = None
        self._client = None
        self._collection = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise RagUnavailable(f"sentence-transformers 未安装: {e}") from e
            try:
                self._model = SentenceTransformer(_MODEL_NAME)
            except Exception as e:
                raise RagUnavailable(f"bge-m3 加载失败: {e}") from e
        return self._model

    @property
    def collection(self):
        if self._collection is None:
            try:
                import chromadb
            except ImportError as e:
                raise RagUnavailable(f"chromadb 未安装: {e}") from e
            _PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(_PERSIST_DIR))
            self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)
        return self._collection

    def index_resource(
        self,
        *,
        resource_id: int,
        concept_code: str,
        title: str,
        summary: str | None,
        type: str,
        url: str | None,
        estimated_minutes: int,
    ) -> None:
        doc = (title + "\n\n" + (summary or "")).strip()
        emb = self.model.encode([doc], show_progress_bar=False).tolist()
        self.collection.upsert(
            ids=[str(resource_id)],
            embeddings=emb,
            documents=[doc],
            metadatas=[{
                "resource_id": resource_id,
                "concept_code": concept_code,
                "title": title,
                "type": type,
                "url": url or "",
                "estimated_minutes": int(estimated_minutes or 0),
            }],
        )

    def bootstrap_index(self, db_session) -> int:
        from app.models import Resource

        resources = db_session.query(Resource).all()
        for r in resources:
            self.index_resource(
                resource_id=r.id,
                concept_code=r.concept_code,
                title=r.title,
                summary=r.summary,
                type=r.type,
                url=r.url,
                estimated_minutes=r.estimated_minutes,
            )
        return len(resources)

    def retrieve(
        self, concept_code: str | None, query: str, k: int = 5
    ) -> list[dict[str, Any]]:
        try:
            emb = self.model.encode([query], show_progress_bar=False).tolist()
            params: dict[str, Any] = {"query_embeddings": emb, "n_results": k}
            if concept_code:
                params["where"] = {"concept_code": concept_code}
            res = self.collection.query(**params)
        except RagUnavailable:
            return []
        except Exception as e:
            logger.warning("rag retrieve failed: %s", e)
            return []

        metas = (res or {}).get("metadatas") or []
        if not metas or not metas[0]:
            return []
        return metas[0]


_RAG: RagAdapter | None = None


def get_rag() -> RagAdapter:
    global _RAG
    if _RAG is None:
        _RAG = RagAdapter()
    return _RAG
