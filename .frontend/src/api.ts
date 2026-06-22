/**
 * Generic REST client shared by all three services. Every call is parametrized
 * by a ServiceConfig, so the same functions drive customers, workers and partners.
 */
import type { ServiceConfig } from '@/services'

export type Record_ = Record<string, any>

async function request (url: string, options?: RequestInit) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch { /* response had no JSON body */ }
    throw new Error(detail)
  }

  if (res.status === 204) return null
  return res.json()
}

export function listRecords (svc: ServiceConfig): Promise<Record_[]> {
  return request(`${svc.baseUrl}/${svc.resource}/`)
}

export function createRecord (svc: ServiceConfig, payload: Record_) {
  return request(`${svc.baseUrl}/${svc.resource}/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateRecord (svc: ServiceConfig, id: number, payload: Record_) {
  return request(`${svc.baseUrl}/${svc.resource}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteRecord (svc: ServiceConfig, id: number) {
  return request(`${svc.baseUrl}/${svc.resource}/${id}`, { method: 'DELETE' })
}

export function checkHealth (svc: ServiceConfig) {
  return request(`${svc.baseUrl}/health`)
}
