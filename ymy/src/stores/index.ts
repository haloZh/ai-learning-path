import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { ProfileResponse, Question, Concept, PathItem, Evaluation } from '@/types'
import * as api from '@/api/endpoints'

// sessionStorage 持久化工具:刷新页面不丢学生 + 诊断 + 路径
const SS_KEY = 'lp:state:v1'

interface PersistedState {
  studentId?: number | null
  profile?: ProfileResponse | null
  mastery?: Record<string, number>
  path?: PathItem[]
  reasoning?: string[]
  isMock?: boolean
  isSubmitted?: boolean
  evaluation?: Evaluation | null
}

function loadPersisted(): PersistedState {
  try {
    const raw = sessionStorage.getItem(SS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function savePersisted(patch: PersistedState) {
  try {
    const cur = loadPersisted()
    sessionStorage.setItem(SS_KEY, JSON.stringify({ ...cur, ...patch }))
  } catch {}
}

export function clearPersisted() {
  try { sessionStorage.removeItem(SS_KEY) } catch {}
}

const persisted = loadPersisted()

export const useStudentStore = defineStore('student', () => {
  const profile = ref<ProfileResponse | null>(persisted.profile || null)
  const studentId = ref<number | null>(persisted.studentId || null)
  const isProfileComplete = computed(() => !!profile.value)

  async function createProfile(data: any) {
    const res = await api.createProfile(data)
    profile.value = res
    studentId.value = res.id
    return res
  }

  async function fetchProfile(id: number) {
    const res = await api.getProfile(id)
    profile.value = res
    studentId.value = res.id
    return res
  }

  watch([profile, studentId], () => {
    savePersisted({ profile: profile.value, studentId: studentId.value })
  })

  return { profile, studentId, isProfileComplete, createProfile, fetchProfile }
})

export const useDiagnoseStore = defineStore('diagnose', () => {
  const questions = ref<Question[]>([])
  const answers = ref<Record<number, string>>({})
  const answerStartTimes = ref<Record<number, number>>({})
  const mastery = ref<Record<string, number>>(persisted.mastery || {})
  const path = ref<PathItem[]>(persisted.path || [])
  const reasoning = ref<string[]>(persisted.reasoning || [])
  const evaluation = ref<Evaluation | null>(persisted.evaluation || null)
  const isMock = ref<boolean>(persisted.isMock || false)
  const isSubmitted = ref<boolean>(persisted.isSubmitted || false)
  const isLoading = ref(false)

  const isDiagnosed = computed(() => Object.keys(mastery.value).length > 0)

  async function fetchQuestions(n: number = 5) {
    const qs = await api.getSampleQuestions(n)
    questions.value = qs
    answers.value = {}
    answerStartTimes.value = {}
    // 进入题目时记开始时间(切题用 startTimer 重置)
    qs.forEach(q => { answerStartTimes.value[q.id] = Date.now() })
    isSubmitted.value = false
  }

  function setAnswer(questionId: number, answer: string) {
    answers.value[questionId] = answer
  }

  function startTimer(questionId: number) {
    if (!answerStartTimes.value[questionId]) {
      answerStartTimes.value[questionId] = Date.now()
    }
  }

  function reset() {
    questions.value = []
    answers.value = {}
    answerStartTimes.value = {}
    mastery.value = {}
    path.value = []
    reasoning.value = []
    evaluation.value = null
    isMock.value = false
    isSubmitted.value = false
  }

  async function submitDiagnose(studentId: number) {
    isLoading.value = true
    try {
      const diagnoseAnswers = questions.value.map(q => {
        const userAnswer = answers.value[q.id]
        const startTime = answerStartTimes.value[q.id] || Date.now()
        const seconds = Math.round((Date.now() - startTime) / 1000)
        return {
          question_id: q.id,
          concept_id: q.concept_code,
          correct: userAnswer === q.answer,
          seconds: Math.max(1, seconds),
        }
      })

      const res = await api.submitDiagnose({
        student_id: studentId,
        answers: diagnoseAnswers,
      })

      mastery.value = res.mastery
      path.value = res.path
      reasoning.value = res.reasoning
      evaluation.value = res.evaluation || null
      isMock.value = res.mock
      isSubmitted.value = true
      return res
    } finally {
      isLoading.value = false
    }
  }

  watch([mastery, path, reasoning, evaluation, isMock, isSubmitted], () => {
    savePersisted({
      mastery: mastery.value,
      path: path.value,
      reasoning: reasoning.value,
      evaluation: evaluation.value,
      isMock: isMock.value,
      isSubmitted: isSubmitted.value,
    })
  }, { deep: true })

  return {
    questions, answers, mastery, path, reasoning, evaluation,
    isMock, isSubmitted, isLoading, isDiagnosed,
    fetchQuestions, setAnswer, startTimer, submitDiagnose, reset,
  }
})

export const usePathStore = defineStore('path', () => {
  const pathData = ref<PathItem[]>(persisted.path || [])
  const concepts = ref<Concept[]>([])
  const isMock = ref<boolean>(persisted.isMock || false)
  const isPathGenerated = computed(() => pathData.value.length > 0)

  async function fetchPath(studentId: number) {
    const res = await api.getPath(studentId)
    pathData.value = res.path
    isMock.value = res.mock
    return res
  }

  async function fetchConcepts(subject?: string) {
    const res = await api.getConcepts(subject)
    concepts.value = res
    return res
  }

  function setPath(data: PathItem[]) {
    pathData.value = data
  }

  return { pathData, concepts, isMock, isPathGenerated, fetchPath, fetchConcepts, setPath }
})

export const useLearnStore = defineStore('learn', () => {
  const currentPath = ref<PathItem[]>([])
  const newPath = ref<PathItem[]>([])
  const reasoning = ref<string[]>([])
  const isMock = ref(false)
  const showAdjustment = ref(false)
  const adjustmentReason = ref('')
  const isLoading = ref(false)
  // 完成状态:用 concept_id::title 作 key
  const completedKeys = ref<Set<string>>(new Set())
  // 用户从路径页点击进入时定位的 idx
  const initialIdx = ref<number>(0)

  async function submitInteraction(studentId: number, event: 'struggle' | 'mastered' | 'skip', conceptId: string, detail: string | null) {
    isLoading.value = true
    try {
      const res = await api.submitInteraction({
        student_id: studentId,
        event,
        concept_id: conceptId,
        detail,
      })
      newPath.value = res.path
      reasoning.value = res.reasoning
      isMock.value = res.mock
      showAdjustment.value = true
      adjustmentReason.value = res.reasoning.join('\n')
      return res
    } finally {
      isLoading.value = false
    }
  }

  // 接受调整:用新路径覆盖
  function acceptAdjustment() {
    showAdjustment.value = false
    currentPath.value = [...newPath.value]
  }

  // 拒绝调整:保留旧路径
  function rejectAdjustment() {
    showAdjustment.value = false
    newPath.value = []
  }

  function setCurrentPath(data: PathItem[]) {
    currentPath.value = data
  }

  function toggleCompleted(key: string) {
    const s = new Set(completedKeys.value)
    if (s.has(key)) s.delete(key)
    else s.add(key)
    completedKeys.value = s
  }

  function isCompleted(key: string) {
    return completedKeys.value.has(key)
  }

  function setInitialIdx(i: number) {
    initialIdx.value = Math.max(0, i)
  }

  return {
    currentPath, newPath, reasoning, isMock, showAdjustment, adjustmentReason, isLoading,
    completedKeys, initialIdx,
    submitInteraction, acceptAdjustment, rejectAdjustment, setCurrentPath,
    toggleCompleted, isCompleted, setInitialIdx,
  }
})

export const useAssessStore = defineStore('assess', () => {
  const mastery = ref<Record<string, number>>(persisted.mastery || {})
  const path = ref<PathItem[]>(persisted.path || [])
  const reasoning = ref<string[]>(persisted.reasoning || [])
  const evaluation = ref<Evaluation | null>(persisted.evaluation || null)
  const isMock = ref<boolean>(persisted.isMock || false)
  const isLoaded = computed(() => Object.keys(mastery.value).length > 0)

  function setFromDiagnose(
    m: Record<string, number>,
    p: PathItem[],
    r: string[],
    mock: boolean,
    ev?: Evaluation | null,
  ) {
    mastery.value = m
    path.value = p
    reasoning.value = r
    isMock.value = mock
    evaluation.value = ev || null
  }

  return { mastery, path, reasoning, evaluation, isMock, isLoaded, setFromDiagnose }
})
