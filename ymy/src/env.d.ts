/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'katex/dist/contrib/auto-render.mjs' {
  const renderMathInElement: (el: HTMLElement, options?: any) => void
  export default renderMathInElement
}
