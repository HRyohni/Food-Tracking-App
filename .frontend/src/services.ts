/**
 * Central registry of the three backend services this single frontend talks to.
 * Each entry is fully self-describing (base URL, REST resource, form fields), so
 * the UI is generic and renders tables/forms straight from this config.
 *
 * Base URLs can be overridden at build time via VITE_* env vars (see .env).
 */

export interface Field {
  key: string
  label: string
  type?: 'text' | 'email' | 'password'
  required?: boolean
}

export interface ServiceConfig {
  key: string
  label: string
  /** Singular noun used for dialog titles, e.g. "Customer". */
  singular: string
  icon: string
  baseUrl: string
  /** REST path segment, e.g. "customers". */
  resource: string
  /** Fields sent when creating a record (incl. password). */
  fields: Field[]
  /** Which field holds the email used to log in (customers/workers: "email",
   *  partners: "contact_email"). */
  emailKey: string
}

/** Look up a service config by its key (throws if unknown). */
export function serviceByKey (key: string): ServiceConfig {
  const svc = services.find(s => s.key === key)
  if (!svc) throw new Error(`Unknown service: ${key}`)
  return svc
}

const env = import.meta.env

export const services: ServiceConfig[] = [
  {
    key: 'customer',
    label: 'Customers',
    singular: 'Customer',
    icon: 'mdi-account',
    baseUrl: env.VITE_CUSTOMER_API ?? 'http://localhost:8001',
    resource: 'customers',
    emailKey: 'email',
    fields: [
      { key: 'name', label: 'Name', required: true },
      { key: 'email', label: 'Email', type: 'email', required: true },
      { key: 'phone', label: 'Phone' },
      { key: 'password', label: 'Password', type: 'password', required: true },
    ],
  },
  {
    key: 'worker',
    label: 'Workers',
    singular: 'Worker',
    icon: 'mdi-account-hard-hat',
    baseUrl: env.VITE_WORKER_API ?? 'http://localhost:8002',
    resource: 'workers',
    emailKey: 'email',
    fields: [
      { key: 'name', label: 'Name', required: true },
      { key: 'email', label: 'Email', type: 'email', required: true },
      { key: 'phone', label: 'Phone' },
      { key: 'specialty', label: 'Specialty' },
      { key: 'password', label: 'Password', type: 'password', required: true },
    ],
  },
  {
    key: 'partner',
    label: 'Partners',
    singular: 'Partner',
    icon: 'mdi-handshake',
    baseUrl: env.VITE_PARTNER_API ?? 'http://localhost:8003',
    resource: 'partners',
    emailKey: 'contact_email',
    fields: [
      { key: 'company_name', label: 'Company name', required: true },
      { key: 'contact_email', label: 'Contact email', type: 'email', required: true },
      { key: 'phone', label: 'Phone' },
      { key: 'password', label: 'Password', type: 'password', required: true },
    ],
  },
]
