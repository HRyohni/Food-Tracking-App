/**
 * Per-service auth state. Each backend (customer/partner/worker) has its own
 * token + current user, persisted to localStorage so a refresh keeps you signed
 * in. A customer token is only valid on the customer API, etc.
 */
import { reactive } from 'vue'
import { loginRequest, meRequest } from '@/api'
import { services, type ServiceConfig } from '@/services'

export interface AuthState {
  token: string | null
  user: Record<string, any> | null
}

const state: Record<string, AuthState> = reactive({})
for (const s of services) {
  state[s.key] = { token: localStorage.getItem(`token:${s.key}`), user: null }
}

export function auth (key: string): AuthState {
  return state[key]
}

export async function doLogin (svc: ServiceConfig, email: string, password: string) {
  const data = await loginRequest(svc, email, password)
  state[svc.key].token = data.access_token
  localStorage.setItem(`token:${svc.key}`, data.access_token)
  await loadMe(svc)
}

export async function loadMe (svc: ServiceConfig) {
  const token = state[svc.key].token
  if (!token) return
  try {
    state[svc.key].user = await meRequest(svc, token)
  } catch (e: any) {
    if (e?.status === 401) doLogout(svc) // expired/invalid token
    else throw e
  }
}

export function doLogout (svc: ServiceConfig) {
  state[svc.key].token = null
  state[svc.key].user = null
  localStorage.removeItem(`token:${svc.key}`)
}
