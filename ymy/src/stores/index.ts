import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ProfileResponse, Question, Concept, PathItem, DiagnoseResponse, InteractionResponse } from '@/types'
import * as api from '@/api/endpoints'

export const useStudentStore = defineStore('student', () => {
  const profile = ref<ProfileResponse | null>(null)
  const studentId = ref<number | null>(null)
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

  return { profile, studentId, isProfileComplete, createProfile, fetchProfile }
})

export const useDiagnoseStore = defineStore('diagnose', () => {
  const questions = ref<Question[]>([])
  const answers = ref<Record<number, string>>({})
  const answerTimes = ref<Record<number, number>>({})
  const answerStartTimes = ref<Record<number, number>>({})
  const mastery = ref<Record<string, number>>({})
  const path = ref<PathItem[]>([])
  const reasoning = ref<string[]>([])
  const isMock = ref(false)
  const isSubmitted = ref(false)
  const isLoading = ref(false)

  const isDiagnosed = computed(() => Object.keys(mastery.value).length > 0)

  async function fetchQuestions(n: number = 5) {
    const qs = await api.getSampleQuestions(n)
    questions.value = qs
    answers.value = {}
    answerTimes.value = {}
    answerStartTimes.value = {}
    isSubmitted.value = false
  }

  function setAnswer(questionId: number, answer: string) {
    answers.value[questionId] = answer
    if (!answerStartTimes.value[questionId]) {
      answerStartTimes.value[questionId] = Date.now()
    }
  }

  function startTimer(questionId: number) {
    answerStartTimes.value[questionId] = Date.now()
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
          seconds: seconds || 30,
        }
      })

      const res = await api.submitDiagnose({
        student_id: studentId,
        answers: diagnoseAnswers,
      })

      mastery.value = res.mastery
      path.value = res.path
      reasoning.value = res.reasoning
      isMock.value = res.mock
      isSubmitted.value = true
      return res
    } finally {
      isLoading.value = false
    }
  }

  return {
    questions, answers, mastery, path, reasoning, isMock, isSubmitted, isLoading,
    isDiagnosed,
    fetchQuestions, setAnswer, startTimer, submitDiagnose,
  }
})

export const usePathStore = defineStore('path', () => {
  const pathData = ref<PathItem[]>([])
  const concepts = ref<Concept[]>([])
  const isMock = ref(false)
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

  function dismissAdjustment() {
    showAdjustment.value = false
    currentPath.value = [...newPath.value]
  }

  function setCurrentPath(data: PathItem[]) {
    currentPath.value = data
  }

  return {
    currentPath, newPath, reasoning, isMock, showAdjustment, adjustmentReason, isLoading,
    submitInteraction, dismissAdjustment, setCurrentPath,
  }
})

export const useAssessStore = defineStore('assess', () => {
  const mastery = ref<Record<string, number>>({})
  const path = ref<PathItem[]>([])
  const reasoning = ref<string[]>([])
  const isMock = ref(false)
  const isLoaded = computed(() => Object.keys(mastery.value).length > 0)

  function setFromDiagnose(m: Record<string, number>, p: PathItem[], r: string[], mock: boolean) {
    mastery.value = m
    path.value = p
    reasoning.value = r
    isMock.value = mock
  }

  return { mastery, path, reasoning, isMock, isLoaded, setFromDiagnose }
})
