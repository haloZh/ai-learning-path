import api from './index'
import type { ProfileRequest, ProfileResponse, Concept, Question, DiagnoseRequest, DiagnoseResponse, PathResponse, InteractionRequest, InteractionResponse, HealthResponse } from '@/types'

export function getHealth() {
  return api.get<any, HealthResponse>('/health')
}

export function createProfile(data: ProfileRequest) {
  return api.post<any, ProfileResponse>('/profile', data)
}

export function getProfile(id: number) {
  return api.get<any, ProfileResponse>(`/profile/${id}`)
}

export function listProfiles() {
  return api.get<any, ProfileResponse[]>('/profile')
}

export function getConcepts(subject?: string) {
  return api.get<any, Concept[]>('/concepts', { params: subject ? { subject } : {} })
}

export function getSampleQuestions(n: number = 5) {
  return api.get<any, Question[]>('/questions/sample', { params: { n } })
}

export function submitDiagnose(data: DiagnoseRequest) {
  return api.post<any, DiagnoseResponse>('/diagnose', data)
}

export function getPath(studentId: number) {
  return api.get<any, PathResponse>(`/path/${studentId}`)
}

export function submitInteraction(data: InteractionRequest) {
  return api.post<any, InteractionResponse>('/interaction', data)
}
