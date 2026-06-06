<template>
  <span ref="elRef" class="katex-render" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import 'katex/dist/katex.min.css'
import katex from 'katex'
import renderMathInElement from 'katex/dist/contrib/auto-render.mjs'

const props = defineProps<{ content: string }>()
const elRef = ref<HTMLElement>()

// 是否含 $...$ / $$...$$ 分隔符
function hasDelimiter(s: string): boolean {
  return /\$.+?\$/.test(s)
}

// 是否像"裸 LaTeX"(无分隔符但含数学命令/上下标),如 \frac{3}{11}、x^2、a_1
function looksLikeBareLatex(s: string): boolean {
  return /\\[a-zA-Z]+|[\^_]\{|\\frac|\\sqrt|\\times|\\div/.test(s)
}

function render() {
  if (!elRef.value) return
  const text = props.content ?? ''

  // 情况 1:含 $ 分隔符 → 用 auto-render 处理混排(中文+公式)
  if (hasDelimiter(text)) {
    elRef.value.textContent = text
    renderMathInElement(elRef.value, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
    })
    return
  }

  // 情况 2:裸 LaTeX(题库选项常见,如 \frac{3}{11})→ 整体当公式渲染
  if (looksLikeBareLatex(text)) {
    try {
      katex.render(text, elRef.value, { throwOnError: false, displayMode: false })
      return
    } catch {
      // 渲染失败则退回纯文本
    }
  }

  // 情况 3:纯文本
  elRef.value.textContent = text
}

onMounted(() => nextTick(render))
watch(() => props.content, () => nextTick(render))
</script>
