/**
 * REST client for all three services. A low-level `apiFetch` handles JSON,
 * bearer tokens, form-encoded login, and error extraction; everything else is a
 * thin domain wrapper over it.
 */
import type { ServiceConfig } from '@/services'

export type Record_ = Record<string, any>

export interface Product {
  id: number
  partner_id: number
  name: string
  description?: string | null
  price: number
  is_available: boolean
  created_at: string
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  unit_price: number
  quantity: number
}

export interface Order {
  id: number
  customer_id: number
  partner_id: number
  worker_id: number | null
  status: string
  delivery_address: string
  total_amount: number
  created_at: string
  updated_at: string
  items: OrderItem[]
}

export interface CourierPing {
  id: number
  order_id: number
  partner_id: number
  delivery_address: string
  acknowledged: boolean
  created_at: string
}

interface Opts {
  method?: string
  body?: any
  token?: string | null
  /** Send body as application/x-www-form-urlencoded (used by OAuth2 login). */
  form?: boolean
}

export async function apiFetch (url: string, opts: Opts = {}): Promise<any> {
  const headers: Record<string, string> = {}
  let body: BodyInit | undefined

  if (opts.form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    body = new URLSearchParams(opts.body).toString()
  } else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`

  const res = await fetch(url, { method: opts.method ?? 'GET', headers, body })

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const j = await res.json()
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch { /* no JSON body */ }
    const err = new Error(detail) as Error & { status?: number }
    err.status = res.status
    throw err
  }

  if (res.status === 204) return null
  return res.json()
}

// ---------- Auth ----------
export const loginRequest = (svc: ServiceConfig, email: string, password: string) =>
  apiFetch(`${svc.baseUrl}/auth/login`, { method: 'POST', form: true, body: { username: email, password } })

export const meRequest = (svc: ServiceConfig, token: string) =>
  apiFetch(`${svc.baseUrl}/me`, { token })

// ---------- Generic CRUD (registration + admin) ----------
export const listRecords = (svc: ServiceConfig): Promise<Record_[]> =>
  apiFetch(`${svc.baseUrl}/${svc.resource}/`)

export const createRecord = (svc: ServiceConfig, payload: Record_) =>
  apiFetch(`${svc.baseUrl}/${svc.resource}/`, { method: 'POST', body: payload })

export const updateRecord = (svc: ServiceConfig, id: number, payload: Record_) =>
  apiFetch(`${svc.baseUrl}/${svc.resource}/${id}`, { method: 'PUT', body: payload })

export const deleteRecord = (svc: ServiceConfig, id: number) =>
  apiFetch(`${svc.baseUrl}/${svc.resource}/${id}`, { method: 'DELETE' })

export const checkHealth = (svc: ServiceConfig) => apiFetch(`${svc.baseUrl}/health`)

// ---------- Customer domain ----------
export const browseProducts = (svc: ServiceConfig, partnerId?: number): Promise<Product[]> =>
  apiFetch(`${svc.baseUrl}/products/${partnerId ? `?partner_id=${partnerId}` : ''}`)

export const placeOrder = (svc: ServiceConfig, token: string, payload: Record_): Promise<Order> =>
  apiFetch(`${svc.baseUrl}/orders/`, { method: 'POST', body: payload, token })

export const myOrders = (svc: ServiceConfig, token: string): Promise<Order[]> =>
  apiFetch(`${svc.baseUrl}/orders/`, { token })

export const cancelOrder = (svc: ServiceConfig, token: string, id: number): Promise<Order> =>
  apiFetch(`${svc.baseUrl}/orders/${id}/cancel`, { method: 'POST', token })

// ---------- Partner domain ----------
export const myProducts = (svc: ServiceConfig, token: string): Promise<Product[]> =>
  apiFetch(`${svc.baseUrl}/products/`, { token })

export const createProduct = (svc: ServiceConfig, token: string, payload: Record_): Promise<Product> =>
  apiFetch(`${svc.baseUrl}/products/`, { method: 'POST', body: payload, token })

export const updateProduct = (svc: ServiceConfig, token: string, id: number, payload: Record_): Promise<Product> =>
  apiFetch(`${svc.baseUrl}/products/${id}`, { method: 'PUT', body: payload, token })

export const deleteProduct = (svc: ServiceConfig, token: string, id: number) =>
  apiFetch(`${svc.baseUrl}/products/${id}`, { method: 'DELETE', token })

export const partnerOrders = (svc: ServiceConfig, token: string, status?: string): Promise<Order[]> =>
  apiFetch(`${svc.baseUrl}/orders/${status ? `?status=${status}` : ''}`, { token })

export const setOrderStatus = (svc: ServiceConfig, token: string, id: number, status: string): Promise<Order> =>
  apiFetch(`${svc.baseUrl}/orders/${id}/status`, { method: 'PATCH', body: { status }, token })

// ---------- Worker / courier domain ----------
export const availableOrders = (svc: ServiceConfig, token: string): Promise<Order[]> =>
  apiFetch(`${svc.baseUrl}/orders/available`, { token })

export const myDeliveries = (svc: ServiceConfig, token: string): Promise<Order[]> =>
  apiFetch(`${svc.baseUrl}/orders/`, { token })

export const acceptOrder = (svc: ServiceConfig, token: string, id: number): Promise<Order> =>
  apiFetch(`${svc.baseUrl}/orders/${id}/accept`, { method: 'POST', token })

export const deliverOrder = (svc: ServiceConfig, token: string, id: number): Promise<Order> =>
  apiFetch(`${svc.baseUrl}/orders/${id}/deliver`, { method: 'POST', token })

export const dispatchPings = (svc: ServiceConfig, token: string): Promise<CourierPing[]> =>
  apiFetch(`${svc.baseUrl}/dispatch/pings`, { token })

export const ackPing = (svc: ServiceConfig, token: string, id: number): Promise<CourierPing> =>
  apiFetch(`${svc.baseUrl}/dispatch/pings/${id}/ack`, { method: 'POST', token })
