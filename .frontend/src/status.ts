/**
 * Shared helpers for rendering order status and the partner status workflow.
 */

export const STATUS_COLOR: Record<string, string> = {
  pending: 'grey',
  accepted: 'blue',
  rejected: 'red',
  preparing: 'orange',
  ready: 'purple',
  picked_up: 'teal',
  delivered: 'green',
  cancelled: 'red',
}

export function statusColor (status: string): string {
  return STATUS_COLOR[status] ?? 'grey'
}

export function statusLabel (status: string): string {
  return status.replace('_', ' ')
}

/**
 * Next status a partner can move an order to, keyed by current status.
 * Mirrors PARTNER_TRANSITIONS on the partner backend.
 */
export const PARTNER_NEXT: Record<string, { status: string, label: string, color: string }[]> = {
  pending: [
    { status: 'accepted', label: 'Accept', color: 'success' },
    { status: 'rejected', label: 'Reject', color: 'error' },
  ],
  accepted: [{ status: 'preparing', label: 'Start preparing', color: 'primary' }],
  preparing: [{ status: 'ready', label: 'Mark ready', color: 'primary' }],
}

export function formatDate (value: string): string {
  return value ? new Date(value).toLocaleString() : ''
}

/** A stable, varied food emoji for a given id — purely decorative. */
const FOOD_EMOJI = ['🍔', '🍕', '🍜', '🌮', '🍣', '🥗', '🍱', '🍟', '🥪', '🍩', '🍰', '🥤', '🍗', '🌯', '🍝', '🥟']
export function foodEmoji (seed: number): string {
  return FOOD_EMOJI[Math.abs(seed) % FOOD_EMOJI.length]
}
