/// <reference types="vite/client" />
/// <reference types="vite-plugin-vue-layouts-next/client" />

interface ImportMetaEnv {
  readonly VITE_CUSTOMER_API?: string
  readonly VITE_WORKER_API?: string
  readonly VITE_PARTNER_API?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
