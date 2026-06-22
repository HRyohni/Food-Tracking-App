<template>
  <LoginCard v-if="!a.token" service-key="partner" />

  <v-container v-else class="py-6" max-width="1100">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h5 font-weight-medium">{{ a.user?.company_name ?? 'Partner' }}</h2>
      <v-spacer />
      <v-btn prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" @click:close="error = ''">
      {{ error }}
    </v-alert>

    <v-tabs v-model="tab" class="mb-4" color="primary">
      <v-tab value="orders">
        Incoming orders
        <v-badge v-if="pendingCount" class="ml-2" color="error" :content="pendingCount" inline />
      </v-tab>
      <v-tab value="menu">Menu</v-tab>
    </v-tabs>

    <!-- ORDERS -->
    <div v-if="tab === 'orders'">
      <v-card v-for="o in orders" :key="o.id" class="mb-2" variant="outlined">
        <v-card-text>
          <div class="d-flex align-center">
            <span class="font-weight-medium">Order #{{ o.id }}</span>
            <v-chip class="ml-2" :color="statusColor(o.status)" size="small" variant="flat">
              {{ statusLabel(o.status) }}
            </v-chip>
            <v-spacer />
            <span class="font-weight-medium">${{ o.total_amount.toFixed(2) }}</span>
          </div>
          <div class="text-caption text-medium-emphasis mt-1">
            {{ o.items.map(i => `${i.quantity}× ${i.product_name}`).join(', ') }} · to {{ o.delivery_address }}
          </div>
          <div class="mt-2">
            <v-btn
              v-for="action in nextActions(o.status)"
              :key="action.status"
              class="mr-2"
              :color="action.color"
              size="small"
              variant="tonal"
              @click="advance(o.id, action.status)"
            >
              {{ action.label }}
            </v-btn>
            <span v-if="!nextActions(o.status).length" class="text-caption text-medium-emphasis">
              {{ o.worker_id ? `Courier #${o.worker_id}` : 'Waiting for courier' }}
            </span>
          </div>
        </v-card-text>
      </v-card>
      <div v-if="!orders.length" class="text-medium-emphasis py-6 text-center">No orders yet.</div>
    </div>

    <!-- MENU -->
    <div v-else>
      <div class="d-flex mb-3">
        <v-spacer />
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">Add product</v-btn>
      </div>
      <v-data-table :headers="headers" :items="products" :loading="loading" item-value="id">
        <template #item.price="{ value }">${{ Number(value).toFixed(2) }}</template>
        <template #item.is_available="{ value }">
          <v-chip :color="value ? 'success' : 'grey'" size="small" variant="tonal">
            {{ value ? 'available' : 'hidden' }}
          </v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
          <v-btn color="error" icon="mdi-delete" size="small" variant="text" @click="remove(item.id)" />
        </template>
      </v-data-table>
    </div>

    <!-- PRODUCT DIALOG -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card :title="editingId ? 'Edit product' : 'New product'">
        <v-card-text>
          <v-text-field v-model="form.name" class="mb-1" density="comfortable" label="Name *" />
          <v-text-field v-model="form.description" class="mb-1" density="comfortable" label="Description" />
          <v-text-field v-model.number="form.price" class="mb-1" density="comfortable" label="Price *" type="number" />
          <v-switch v-model="form.is_available" color="primary" hide-details label="Available" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="saving" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Save</v-btn>
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
  import { PARTNER_NEXT, statusColor, statusLabel } from '@/status'

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

  const headers = [
    { title: 'Name', key: 'name' },
    { title: 'Description', key: 'description' },
    { title: 'Price', key: 'price' },
    { title: 'Status', key: 'is_available' },
    { title: '', key: 'actions', sortable: false },
  ]

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
