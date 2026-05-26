"""LangGraph 编排:两条独立链。

- diagnose 链:diagnose -> plan -> evaluate,首次启动跑一次
  · 末尾追加 evaluate 节点对 path 做客观评分,便于工程迭代追踪
- optimize 链:optimize 单节点,学习过程中每次交互触发
"""

from langgraph.graph import END, StateGraph

from .nodes import diagnose_node, evaluate_node, optimize_node, plan_node
from .state import AgentState


def build_diagnose_graph():
    g = StateGraph(AgentState)
    g.add_node("diagnose", diagnose_node)
    g.add_node("plan", plan_node)
    g.add_node("evaluate", evaluate_node)
    g.set_entry_point("diagnose")
    g.add_edge("diagnose", "plan")
    g.add_edge("plan", "evaluate")
    g.add_edge("evaluate", END)
    return g.compile()


def build_optimize_graph():
    g = StateGraph(AgentState)
    g.add_node("optimize", optimize_node)
    g.set_entry_point("optimize")
    g.add_edge("optimize", END)
    return g.compile()
