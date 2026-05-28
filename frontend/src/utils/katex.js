import renderMathInElement from 'katex/dist/contrib/auto-render.mjs'

export function renderKatex(el) {
  if (!el || !el.isConnected) return
  try {
    renderMathInElement(el, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
      ],
      throwOnError: false,
    })
  } catch (e) {
    console.warn('renderKatex error (suppressed):', e)
  }
}
