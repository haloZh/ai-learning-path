import renderMathInElement from 'katex/dist/contrib/auto-render.mjs'

export function renderKatex(el) {
  if (!el) return
  renderMathInElement(el, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false },
    ],
    throwOnError: false,
  })
}
