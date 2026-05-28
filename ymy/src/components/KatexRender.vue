<template>
  <span ref="elRef" class="katex-render" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import 'katex/dist/katex.min.css'
import renderMathInElement from 'katex/dist/contrib/auto-render.mjs'

const props = defineProps<{ content: string }>()
const elRef = ref<HTMLElement>()

function render() {
  if (!elRef.value) return
  elRef.value.textContent = props.content
  renderMathInElement(elRef.value, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false },
    ],
    throwOnError: false,
  })
}

onMounted(() => nextTick(render))
watch(() => props.content, () => nextTick(render))
</script>
