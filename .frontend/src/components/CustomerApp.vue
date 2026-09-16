<template>
  <LoginCard v-if="!a.token" service-key="customer" />

  <v-container v-else class="py-6" max-width="1200">
    <!-- Hero -->
    <div class="wolt-hero mb-6">
      <div class="d-flex align-center">
        <div>
          <div class="wolt-hero__title">Hi, {{ a.user?.name ?? 'there' }} 👋</div>
          <div class="wolt-hero__sub">
            {{ selectedPartner === null ? 'Pick a restaurant to get started' : `Browsing ${selectedPartnerName}` }}
          </div>
        </div>
        <v-spacer />
        <v-btn color="white" prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
      </div>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" variant="tonal" @click:close="error = ''">
      {{ error }}
    </v-alert>

    <v-row>
      <!-- LEFT: restaurants OR a single restaurant's menu -->
      <v-col cols="12" md="8">
        <!-- Restaurant list -->
        <template v-if="selectedPartner === null">
          <div class="d-flex align-center mb-3">
            <h3 class="wolt-section-title">Restaurants</h3>
            <v-spacer />
            <v-btn icon="mdi-refresh" :loading="loading" size="small" variant="text" @click="loadProducts" />
          </div>

          <v-row>
            <v-col v-for="st in partnerCards" :key="st.id" cols="12" sm="6">
              <v-card class="wolt-hover" elevation="1" height="100%" @click="openPartner(st.id)">
                <v-card-text class="d-flex align-center" style="gap: 16px">
                  <div class="wolt-tile">{{ foodEmoji(st.id) }}</div>
                  <div class="flex-grow-1" style="min-width: 0">
                    <div class="font-weight-bold text-truncate">{{ st.name }}</div>
                    <div class="text-caption text-medium-emphasis">
                      {{ st.count }} item{{ st.count === 1 ? '' : 's' }} · from ${{ st.from.toFixed(2) }}
                    </div>
                  </div>
                  <v-icon class="text-medium-emphasis" icon="mdi-chevron-right" />
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <div v-if="!partnerCards.length && !loading" class="wolt-empty">
            <div class="wolt-empty__emoji">🏪</div>
            No restaurants available yet.
          </div>
        </template>

        <!-- One restaurant's menu -->
        <template v-else>
          <div class="d-flex align-center mb-3" style="gap: 8px">
            <v-btn icon="mdi-arrow-left" size="small" variant="tonal" @click="backToPartners" />
            <div class="wolt-tile">{{ foodEmoji(selectedPartner) }}</div>
            <h3 class="wolt-section-title text-truncate">{{ selectedPartnerName }}</h3>
            <v-spacer />
            <v-btn icon="mdi-refresh" :loading="loading" size="small" variant="text" @click="loadProducts" />
          </div>

          <v-card v-for="p in partnerMenu" :key="p.id" class="mb-3 wolt-hover" elevation="1">
            <v-card-text class="d-flex align-center" style="gap: 16px">
              <div class="wolt-tile">{{ foodEmoji(p.id) }}</div>
              <div class="flex-grow-1" style="min-width: 0">
                <div class="font-weight-bold">{{ p.name }}</div>
                <div class="text-caption text-medium-emphasis text-truncate">{{ p.description || '—' }}</div>
                <span class="wolt-price mt-2 d-inline-block">${{ p.price.toFixed(2) }}</span>
              </div>
              <v-btn color="primary" icon="mdi-plus" size="small" variant="flat" @click="addToCart(p)" />
            </v-card-text>
          </v-card>

          <div v-if="!partnerMenu.length && !loading" class="wolt-empty">
            <div class="wolt-empty__emoji">🍽️</div>
            This restaurant has no dishes right now.
          </div>
        </template>
      </v-col>

      <!-- RIGHT: cart + orders (always visible) -->
      <v-col cols="12" md="4">
        <div class="wolt-sticky">
          <v-card class="mb-4" elevation="2">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" icon="mdi-cart-outline" />
              Your cart
              <v-spacer />
              <v-chip v-if="cartCount" color="primary" size="small" variant="flat">{{ cartCount }}</v-chip>
            </v-card-title>
            <v-card-text>
              <div v-if="!cart.length" class="text-medium-emphasis py-2">Your cart is empty.</div>
              <div v-for="line in cart" :key="line.product.id" class="d-flex align-center mb-2">
                <div class="flex-grow-1 text-truncate">{{ line.product.name }}</div>
                <v-btn density="comfortable" icon="mdi-minus" size="x-small" variant="tonal" @click="changeQty(line, -1)" />
                <span class="mx-2 font-weight-bold">{{ line.qty }}</span>
                <v-btn density="comfortable" icon="mdi-plus" size="x-small" variant="tonal" @click="changeQty(line, 1)" />
                <span class="ml-3 font-weight-medium" style="width: 64px; text-align: right">
                  ${{ (line.product.price * line.qty).toFixed(2) }}
                </span>
              </div>

              <template v-if="cart.length">
                <v-divider class="my-3" />
                <div class="d-flex align-center mb-3">
                  <span class="text-h6 font-weight-bold">Total</span>
                  <v-spacer />
                  <span class="text-h6 font-weight-bold">${{ cartTotal.toFixed(2) }}</span>
                </div>
                <v-text-field
                  v-model="address"
                  label="Delivery address"
                  prepend-inner-icon="mdi-map-marker-outline"
                />
              </template>
            </v-card-text>
            <v-card-actions v-if="cart.length" class="px-4 pb-4">
              <v-btn variant="text" @click="cart = []">Clear</v-btn>
              <v-spacer />
              <v-btn color="primary" :disabled="!address" :loading="placing" size="large" variant="flat" @click="checkout">
                Place order · ${{ cartTotal.toFixed(2) }}
              </v-btn>
            </v-card-actions>
          </v-card>

          <div class="d-flex align-center mb-3">
            <h3 class="wolt-section-title">My orders</h3>
            <v-spacer />
            <v-btn icon="mdi-refresh" size="small" variant="text" @click="loadOrders" />
          </div>

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
              <div class="text-caption text-medium-emphasis mt-1">
                {{ o.items.map(i => `${i.quantity}× ${i.product_name}`).join(', ') }}
              </div>
              <v-btn
                v-if="o.status === 'pending'"
                class="mt-2"
                color="error"
                size="small"
                variant="text"
                @click="cancel(o.id)"
              >
                Cancel order
              </v-btn>
            </v-card-text>
          </v-card>
          <div v-if="!orders.length" class="wolt-empty">
            <div class="wolt-empty__emoji">🧾</div>
            No orders yet.
          </div>
        </div>
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
  import { foodEmoji, statusColor, statusLabel } from '@/status'

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
  // null = showing the restaurant list; otherwise the partner_id being viewed.
  const selectedPartner = ref<number | null>(null)
  let timer: number | undefined

  const cartTotal = computed(() => cart.value.reduce((s, l) => s + l.product.price * l.qty, 0))
  const cartCount = computed(() => cart.value.reduce((s, l) => s + l.qty, 0))
  const cartPartner = computed(() => cart.value[0]?.product.partner_id ?? null)

  // One card per partner that has available items, with item count + cheapest price.
  const partnerCards = computed(() => {
    const map = new Map<number, { id: number, name: string, count: number, from: number }>()
    for (const p of products.value) {
      const e = map.get(p.partner_id) ?? { id: p.partner_id, name: partnerName(p.partner_id), count: 0, from: Infinity }
      e.count++
      e.from = Math.min(e.from, p.price)
      map.set(p.partner_id, e)
    }
    return [...map.values()].sort((x, y) => x.name.localeCompare(y.name))
  })

  const partnerMenu = computed(() =>
    products.value.filter(p => p.partner_id === selectedPartner.value),
  )
  const selectedPartnerName = computed(() =>
    selectedPartner.value === null ? '' : partnerName(selectedPartner.value),
  )

  function partnerName (id: number) {
    return partners.value[id] ?? `Partner #${id}`
  }

  function openPartner (id: number) {
    selectedPartner.value = id
    error.value = ''
  }

  function backToPartners () {
    selectedPartner.value = null
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
      error.value = 'An order can only contain items from one restaurant. Clear your cart first.'
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
