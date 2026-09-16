<template>
  <LoginCard v-if="!a.token" service-key="partner" />

  <v-container v-else class="py-6" max-width="1200">
    <!-- Hero -->
    <div class="wolt-hero mb-6">
      <div class="d-flex align-center">
        <div class="wolt-tile wolt-tile--lg mr-4" style="background: rgba(255,255,255,.18)">🏪</div>
        <div>
          <div class="wolt-hero__title">{{ a.user?.company_name ?? 'Partner' }}</div>
          <div class="wolt-hero__sub">
            {{ pendingCount ? `${pendingCount} order(s) waiting for you` : 'All caught up — nice work' }}
          </div>
        </div>
        <v-spacer />
        <v-btn color="white" prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
      </div>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" variant="tonal" @click:close="error = ''">
      {{ error }}
    </v-alert>

    <v-tabs v-model="tab" class="mb-5" color="primary">
      <v-tab value="orders">
        Incoming orders
        <v-badge v-if="pendingCount" class="ml-2" color="error" :content="pendingCount" inline />
      </v-tab>
      <v-tab value="menu">Menu</v-tab>
    </v-tabs>

    <!-- ORDERS -->
    <div v-if="tab === 'orders'">
      <v-card v-for="o in orders" :key="o.id" class="mb-3" elevation="1">
        <v-card-text>
          <div class="d-flex align-center">
            <span class="font-weight-bold">Order #{{ o.id }}</span>
            <v-chip class="ml-2" :color="statusColor(o.status)" size="small" variant="flat">
              {{ statusLabel(o.status) }}
            </v-chip>
            <v-spacer />
            <span class="font-weight-bold">${{ o.total_amount.toFixed(2) }}</span>
          </div>
          <div class="text-body-2 mt-2">
            {{ o.items.map(i => `${i.quantity}× ${i.product_name}`).join(', ') }}
          </div>
          <div class="text-caption text-medium-emphasis mt-1">
            <v-icon icon="mdi-map-marker-outline" size="14" /> {{ o.delivery_address }}
          </div>
          <div class="mt-3">
            <v-btn
              v-for="action in nextActions(o.status)"
              :key="action.status"
              class="mr-2"
              :color="action.color"
              size="small"
              variant="flat"
              @click="advance(o.id, action.status)"
            >
              {{ action.label }}
            </v-btn>
            <v-chip v-if="!nextActions(o.status).length" size="small" variant="tonal">
              {{ o.worker_id ? `Courier #${o.worker_id}` : 'Waiting for courier' }}
            </v-chip>
          </div>
        </v-card-text>
      </v-card>
      <div v-if="!orders.length" class="wolt-empty">
        <div class="wolt-empty__emoji">📦</div>
        No orders yet.
      </div>
    </div>

    <!-- MENU -->
    <div v-else>
      <div class="d-flex align-center mb-3">
        <h3 class="wolt-section-title">Your products</h3>
        <v-spacer />
        <v-btn color="primary" prepend-icon="mdi-plus" variant="flat" @click="openCreate">Add product</v-btn>
      </div>

      <v-card v-for="p in products" :key="p.id" class="mb-3" elevation="1">
        <v-card-text class="d-flex align-center" style="gap: 16px">
          <div class="wolt-tile">{{ foodEmoji(p.id) }}</div>
          <div class="flex-grow-1" style="min-width: 0">
            <div class="d-flex align-center">
              <span class="font-weight-bold">{{ p.name }}</span>
              <v-chip class="ml-2" :color="p.is_available ? 'success' : 'grey'" size="x-small" variant="tonal">
                {{ p.is_available ? 'available' : 'hidden' }}
              </v-chip>
            </div>
            <div class="text-caption text-medium-emphasis text-truncate">{{ p.description || '—' }}</div>
            <span class="wolt-price mt-2 d-inline-block">${{ Number(p.price).toFixed(2) }}</span>
          </div>
          <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(p)" />
          <v-btn color="error" icon="mdi-delete-outline" size="small" variant="text" @click="remove(p.id)" />
        </v-card-text>
      </v-card>
      <div v-if="!products.length && !loading" class="wolt-empty">
        <div class="wolt-empty__emoji">🍳</div>
        No products yet — add your first dish.
      </div>
    </div>

    <!-- PRODUCT DIALOG -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card :title="editingId ? 'Edit product' : 'New product'">
        <v-card-text>
          <v-text-field v-model="form.name" class="mb-3" label="Name *" />
          <v-text-field v-model="form.description" class="mb-3" label="Description" />
          <v-text-field v-model.number="form.price" class="mb-3" label="Price *" prefix="$" type="number" />
          <v-switch v-model="form.is_available" color="primary" hide-details label="Available" />
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer />
          <v-btn :disabled="saving" variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" variant="flat" @click="save">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
  import {
    createProduct,
    deleteProduct,
    myProducts,
    type Order,
    partnerOrders,
    type Product,
    type Record_,
    setOrderStatus,
    updateProduct,
  } from '@/api'
  import { auth, doLogout, loadMe } from '@/auth'
  import LoginCard from '@/components/LoginCard.vue'
  import { serviceByKey } from '@/services'
  import { foodEmoji, PARTNER_NEXT, statusColor, statusLabel } from '@/status'

  const svc = serviceByKey('partner')
  const a = auth('partner')

  const tab = ref('orders')
  const products = ref<Product[]>([])
  const orders = ref<Order[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const dialog = ref(false)
  const editingId = ref<number | null>(null)
  const form = reactive<Record_>({ name: '', description: '', price: 0, is_available: true })
  let timer: number | undefined

  const pendingCount = computed(() => orders.value.filter(o => o.status === 'pending').length)

  function nextActions (status: string) {
    return PARTNER_NEXT[status] ?? []
  }

  async function loadProducts () {
    if (!a.token) return
    loading.value = true
    try {
      products.value = await myProducts(svc, a.token)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadOrders () {
    if (!a.token) return
    try {
      orders.value = await partnerOrders(svc, a.token)
    } catch (e: any) {
      error.value = e.message
    }
  }

  function openCreate () {
    editingId.value = null
    Object.assign(form, { name: '', description: '', price: 0, is_available: true })
    error.value = ''
    dialog.value = true
  }

  function openEdit (p: Product) {
    editingId.value = p.id
    Object.assign(form, { name: p.name, description: p.description ?? '', price: p.price, is_available: p.is_available })
    error.value = ''
    dialog.value = true
  }

  async function save () {
    if (!a.token) return
    saving.value = true
    error.value = ''
    try {
      if (editingId.value) await updateProduct(svc, a.token, editingId.value, { ...form })
      else await createProduct(svc, a.token, { ...form })
      dialog.value = false
      await loadProducts()
    } catch (e: any) {
      error.value = e.message
    } finally {
      saving.value = false
    }
  }

  async function remove (id: number) {
    if (!a.token) return
    try {
      await deleteProduct(svc, a.token, id)
      await loadProducts()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function advance (id: number, status: string) {
    if (!a.token) return
    try {
      await setOrderStatus(svc, a.token, id, status)
      await loadOrders()
    } catch (e: any) {
      error.value = e.message
    }
  }

  function logout () {
    doLogout(svc)
  }

  onMounted(async () => {
    await loadMe(svc)
    await loadProducts()
    await loadOrders()
    timer = window.setInterval(loadOrders, 4000)
  })
  onUnmounted(() => clearInterval(timer))
</script>
