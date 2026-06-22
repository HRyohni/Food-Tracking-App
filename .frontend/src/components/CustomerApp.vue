<template>
  <LoginCard v-if="!a.token" service-key="customer" />

  <v-container v-else class="py-6" max-width="1100">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h5 font-weight-medium">Hi, {{ a.user?.name ?? 'there' }}</h2>
      <v-spacer />
      <v-btn prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" @click:close="error = ''">
      {{ error }}
    </v-alert>

    <v-row>
      <!-- Menu -->
      <v-col cols="12" md="7">
        <div class="d-flex align-center mb-2">
          <h3 class="text-h6">Menu</h3>
          <v-spacer />
          <v-btn icon="mdi-refresh" :loading="loading" size="small" variant="text" @click="loadProducts" />
        </div>
        <v-card v-for="p in products" :key="p.id" class="mb-2" variant="outlined">
          <v-card-text class="d-flex align-center">
            <div>
              <div class="font-weight-medium">{{ p.name }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ partnerName(p.partner_id) }} · {{ p.description || '—' }}
              </div>
            </div>
            <v-spacer />
            <span class="mr-4 font-weight-medium">${{ p.price.toFixed(2) }}</span>
            <v-btn color="primary" size="small" variant="tonal" @click="addToCart(p)">Add</v-btn>
          </v-card-text>
        </v-card>
        <div v-if="!products.length && !loading" class="text-medium-emphasis py-6 text-center">
          No products available yet.
        </div>
      </v-col>

      <!-- Cart + orders -->
      <v-col cols="12" md="5">
        <v-card class="mb-4" variant="outlined">
          <v-card-title class="text-subtitle-1">Your cart</v-card-title>
          <v-card-text>
            <div v-if="!cart.length" class="text-medium-emphasis">Cart is empty.</div>
            <div v-for="line in cart" :key="line.product.id" class="d-flex align-center mb-2">
              <div class="flex-grow-1">{{ line.product.name }}</div>
              <v-btn density="comfortable" icon="mdi-minus" size="x-small" variant="text" @click="changeQty(line, -1)" />
              <span class="mx-1">{{ line.qty }}</span>
              <v-btn density="comfortable" icon="mdi-plus" size="x-small" variant="text" @click="changeQty(line, 1)" />
              <span class="ml-3" style="width: 64px; text-align: right">
                ${{ (line.product.price * line.qty).toFixed(2) }}
              </span>
            </div>
            <v-divider v-if="cart.length" class="my-2" />
            <div v-if="cart.length" class="d-flex font-weight-medium">
              <span>Total</span><v-spacer /><span>${{ cartTotal.toFixed(2) }}</span>
            </div>
            <v-text-field
              v-if="cart.length"
              v-model="address"
              class="mt-3"
              density="comfortable"
              hide-details
              label="Delivery address"
            />
          </v-card-text>
          <v-card-actions v-if="cart.length">
            <v-btn variant="text" @click="cart = []">Clear</v-btn>
            <v-spacer />
            <v-btn color="primary" :disabled="!address" :loading="placing" variant="flat" @click="checkout">
              Place order
            </v-btn>
          </v-card-actions>
        </v-card>

        <div class="d-flex align-center mb-2">
          <h3 class="text-h6">My orders</h3>
          <v-spacer />
          <v-btn icon="mdi-refresh" size="small" variant="text" @click="loadOrders" />
        </div>
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
              {{ o.items.map(i => `${i.quantity}× ${i.product_name}`).join(', ') }}
            </div>
            <v-btn
              v-if="o.status === 'pending'"
              class="mt-2"
              color="error"
              size="x-small"
              variant="text"
              @click="cancel(o.id)"
            >
              Cancel
            </v-btn>
          </v-card-text>
        </v-card>
        <div v-if="!orders.length" class="text-medium-emphasis py-4 text-center">No orders yet.</div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref } from 'vue'
  import {
    browseProducts,
    cancelOrder,
    listRecords,
    myOrders,
    type Order,
    placeOrder,
    type Product,
  } from '@/api'
  import { auth, doLogout, loadMe } from '@/auth'
  import LoginCard from '@/components/LoginCard.vue'
  import { serviceByKey } from '@/services'
  import { statusColor, statusLabel } from '@/status'

  interface CartLine { product: Product, qty: number }

  const svc = serviceByKey('customer')
  const partnerSvc = serviceByKey('partner')
  const a = auth('customer')

  const products = ref<Product[]>([])
  const partners = ref<Record<number, string>>({})
  const orders = ref<Order[]>([])
  const cart = ref<CartLine[]>([])
  const address = ref('')
  const loading = ref(false)
  const placing = ref(false)
  const error = ref('')
  let timer: number | undefined

  const cartTotal = computed(() => cart.value.reduce((s, l) => s + l.product.price * l.qty, 0))
  const cartPartner = computed(() => cart.value[0]?.product.partner_id ?? null)

  function partnerName (id: number) {
    return partners.value[id] ?? `Partner #${id}`
  }

  async function loadProducts () {
    loading.value = true
    error.value = ''
    try {
      products.value = await browseProducts(svc)
      const list = await listRecords(partnerSvc)
      partners.value = Object.fromEntries(list.map((p: any) => [p.id, p.company_name]))
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function loadOrders () {
    if (!a.token) return
    try {
      orders.value = await myOrders(svc, a.token)
    } catch (e: any) {
      error.value = e.message
    }
  }

  function addToCart (p: Product) {
    if (cartPartner.value !== null && cartPartner.value !== p.partner_id) {
      error.value = 'An order can only contain items from one partner. Clear your cart first.'
      return
    }
    const line = cart.value.find(l => l.product.id === p.id)
    if (line) line.qty++
    else cart.value.push({ product: p, qty: 1 })
  }

  function changeQty (line: CartLine, delta: number) {
    line.qty += delta
    if (line.qty <= 0) cart.value = cart.value.filter(l => l !== line)
  }

  async function checkout () {
    if (!a.token || cartPartner.value === null) return
    placing.value = true
    error.value = ''
    try {
      await placeOrder(svc, a.token, {
        partner_id: cartPartner.value,
        delivery_address: address.value,
        items: cart.value.map(l => ({ product_id: l.product.id, quantity: l.qty })),
      })
      cart.value = []
      address.value = ''
      await loadOrders()
    } catch (e: any) {
      error.value = e.message
    } finally {
      placing.value = false
    }
  }

  async function cancel (id: number) {
    if (!a.token) return
    try {
      await cancelOrder(svc, a.token, id)
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
    timer = window.setInterval(loadOrders, 4000) // live status
  })
  onUnmounted(() => clearInterval(timer))
</script>
