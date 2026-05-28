export interface ProfileRequest {
  nickname: string
  subject: string
  cognitive_level: 'beginner' | 'intermediate' | 'advanced'
  learning_goal: string
  available_minutes_per_day: number
  learning_style: 'visual' | 'auditory' | 'kinesthetic' | 'reading'
}

export interface ProfileResponse {
  id: number
  nickname: string
  subject: string
  cognitive_level: string
  learning_goal: string
  available_minutes_per_day: number
  learning_style: string
  created_at: string
  updated_at: string
}

export interface Concept {
  code: string
  name: string
  subject: string
  prerequisite_codes: string[]
  description: string
}

export interface Question {
  id: number
  concept_code: string
  question_type: string
  stem: string
  choices: Record<string, string>
  answer: string
  difficulty: number
  score: number
  explanation: string
  source: string
  year: number
}

export interface DiagnoseAnswer {
  question_id: number
  concept_id: string
  correct: boolean
  seconds: number
}

export interface DiagnoseRequest {
  student_id: number
  answers: DiagnoseAnswer[]
}

export interface PathItem {
  concept_id: string
  title: string
  estimated_minutes: number
  reason: string
}

export interface DiagnoseResponse {
  student_id: number
  mastery: Record<string, number>
  path: PathItem[]
  reasoning: string[]
  mock: boolean
}

export interface PathResponse {
  student_id: number
  path: PathItem[]
  mock: boolean
}

export interface InteractionRequest {
  student_id: number
  event: 'struggle' | 'mastered' | 'skip'
  concept_id: string
  detail: string | null
}

export interface InteractionResponse {
  student_id: number
  path: PathItem[]
  reasoning: string[]
  mock: boolean
}

export interface HealthResponse {
  status: string
}
