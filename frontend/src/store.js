import { reactive } from 'vue'

// 全局共享状态,演示用 reactive 已够,无需引入 Pinia
export const store = reactive({
  studentId: null,
  studentNickname: '',
  questions: [],          // [{q: QuestionOut, answer: 'right'|'wrong'|null}]
  diagnoseResult: null,   // {mastery, path, reasoning, mock}
  conceptOptions: [],     // ConceptOut[]
})

export function resetState() {
  store.studentId = null
  store.studentNickname = ''
  store.questions = []
  store.diagnoseResult = null
}
