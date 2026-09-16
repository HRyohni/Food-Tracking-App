/**
 * plugins/vuetify.ts
 *
 * Wolt-inspired theme: bright cyan brand, near-white surfaces on a soft grey
 * page, pill buttons, rounded cards and soft "solo-filled" inputs.
 *
 * Framework documentation: https://vuetifyjs.com
 */

import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'
import '../styles/layers.css'
import 'vuetify/styles'

// Wolt brand cyan + a near-black ink. We override the built-in `light`/`dark`
// themes so the existing theme toggle (theme.cycle) always lands on a Wolt look.
const light = {
  dark: false,
  colors: {
    background: '#F3F4F6',
    surface: '#FFFFFF',
    'surface-variant': '#EBEDF0',
    'on-surface-variant': '#5A5F66',
    primary: '#00C2E8',
    secondary: '#16161E',
    success: '#12B76A',
    warning: '#FB8C00',
    error: '#E5004B',
    info: '#00C2E8',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
    'on-surface': '#16161E',
    'on-background': '#16161E',
  },
}

const dark = {
  dark: true,
  colors: {
    background: '#0E0E13',
    surface: '#1A1A22',
    'surface-variant': '#2A2A35',
    'on-surface-variant': '#A7ABB5',
    primary: '#00C2E8',
    secondary: '#E7E8F0',
    success: '#3DD68C',
    warning: '#FFA726',
    error: '#FF4D7D',
    info: '#00C2E8',
    'on-primary': '#04222B',
    'on-secondary': '#16161E',
    'on-surface': '#ECEDF2',
    'on-background': '#ECEDF2',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: { light, dark },
  },
  defaults: {
    VBtn: { rounded: 'pill', class: 'text-none', style: 'font-weight:600;letter-spacing:0;' },
    VCard: { rounded: 'lg' },
    VChip: { rounded: 'pill' },
    VTextField: { variant: 'solo-filled', flat: true, rounded: 'lg', hideDetails: 'auto' },
    VTextarea: { variant: 'solo-filled', flat: true, rounded: 'lg', hideDetails: 'auto' },
    VSelect: { variant: 'solo-filled', flat: true, rounded: 'lg', hideDetails: 'auto' },
    VAlert: { rounded: 'lg' },
    VAppBar: { flat: true },
  },
  display: {
    mobileBreakpoint: 'md',
    thresholds: {
      xs: 0,
      sm: 600,
      md: 840,
      lg: 1145,
      xl: 1545,
      xxl: 2138,
    },
  },
})
