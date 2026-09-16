<template>
  <LoginCard v-if="!a.token" service-key="worker" />

  <v-container v-else class="py-6" max-width="1200">
    <!-- Hero -->
    <div class="wolt-hero mb-6">
      <div class="d-flex align-center">
        <div class="wolt-tile wolt-tile--lg mr-4" style="background: rgba(255,255,255,.18)">🛵</div>
        <div>
          <div class="wolt-hero__title">Courier · {{ a.user?.name ?? '' }}</div>
          <div class="wolt-hero__sub">{{ available.length }} ready to grab · {{ activeCount }} in progress</div>
        </div>
        <v-spacer />
        <v-btn color="white" prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
      </div>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" variant="tonal" @click:close="error = ''">
      {{ error }}
    </v-alert>

    <!-- Dispatch pings: a partner just accepted an order — head over early. -->
    <v-alert
      v-for="p in pings"
      :key="p.id"
      class="mb-3"
      closable
      icon="mdi-bell-ring"
      type="info"
      variant="tonal"
      @click:close="dismissPing(p.id)"
    >
      <span class="font-weight-bold">Order #{{ p.order_id }} accepted</span> — start heading to {{ p.delivery_address }}.
    </v-alert>

    <v-row>
      <!-- Available pool -->
      <v-col cols="12" md="6">
        <div class="d-flex align-center mb-3">
          <h3 class="wolt-section-title">Available</h3>
          <v-spacer />
          <v-btn icon="mdi-refresh" :loading="loading" size="small" variant="text" @click="loadAll" />
        </div>

        <v-card v-for="o in available" :key="o.id" class="mb-3 wolt-hover" elevation="1">
          <v-card-text>
            <div class="d-flex align-center">
              <span class="font-weight-bold">Order #{{ o.id }}</span>
              <v-spacer />
              <span class="wolt-price">${{ o.total_amount.toFixed(2) }}</span>
            </div>
            <div class="text-caption text-medium-emphasis mt-2">
              <v-icon icon="mdi-package-variant-closed" size="14" />
              {{ o.items.reduce((n, i) => n + i.quantity, 0) }} item(s)
            </div>
            <div class="text-caption text-medium-emphasis">
              <v-icon icon="mdi-map-marker-outline" size="14" /> {{ o.delivery_address }}
            </div>
            <v-btn block class="mt-3" color="primary" variant="flat" @click="accept(o.id)">
              Accept delivery
            </v-btn>
          </v-card-text>
        </v-card>

        <div v-if="!available.length" class="wolt-empty">
          <div class="wolt-empty__emoji">🛵</div>
          No orders ready for pickup.
        </div>
      </v-col>

      <!-- My deliveries -->
      <v-col cols="12" md="6">
        <h3 class="wolt-section-title mb-3">My deliveries</h3>
        <v-card v-for="o in mine" :key="o.id" class="mb-3" elevation="1">
          <v-card-text>
            <div class="d-flex align-center">
              <span class="font-weight-bold">Order #{{ o.id }}</span>
              <v-chip class="ml-2" :color="statusColor(o.status)" size="small" variant="flat">
                {{ statusLabel(o.status) }}
              </v-chip>
              <v-spacer />
              <span class="font-weight-bold">${{ o.total_amount.toFixed(2) }}</span>
            </div>
            <div class="text-caption text-medium-emphasis mt-2">
              <v-icon icon="mdi-map-marker-outline" size="14" /> {{ o.delivery_address }}
            </div>
            <v-btn
              v-if="o.status === 'picked_up'"
              block
              class="mt-3"
              color="success"
              variant="flat"
              @click="deliver(o.id)"
            >
              Mark delivered
            </v-btn>
          </v-card-text>
        </v-card>
        <div v-if="!mine.length" class="wolt-empty">
          <div class="wolt-empty__emoji">✅</div>
          No active deliveries.
        </div>
      </v-col>
    </v-row>

    <!-- Active push: pops the moment a partner accepts a new order. -->
    <v-snackbar v-model="snackbar" color="primary" location="top" :timeout="7000">
      <div class="d-flex align-center">
        <span class="mr-3" style="font-size: 22px">🛵</span>
        <div>
          <div class="font-weight-bold">New delivery — start heading out</div>
          <div class="text-caption">{{ snackMsg }}</div>
        </div>
      </div>
      <template #actions>
        <v-btn variant="text" @click="snackbar = false">Got it</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref } from 'vue'
  import {
    acceptOrder,
    ackPing,
    availableOrders,
    type CourierPing,
    deliverOrder,
    dispatchPings,
    myDeliveries,
    type Order,
  } from '@/api'
  import { auth, doLogout, loadMe } from '@/auth'
  import LoginCard from '@/components/LoginCard.vue'
  import { serviceByKey } from '@/services'
  import { statusColor, statusLabel } from '@/status'

  const svc = serviceByKey('worker')
  const a = auth('worker')

  const available = ref<Order[]>([])
  const mine = ref<Order[]>([])
  const pings = ref<CourierPing[]>([])
  const loading = ref(false)
  const error = ref('')
  const snackbar = ref(false)
  const snackMsg = ref('')
  let timer: number | undefined

  // Track which pings we've already shown so each new accept fires exactly one
  // pop-up. `primed` skips toasting pings that already existed at login.
  const seen = new Set<number>()
  let primed = false

  const activeCount = computed(() => mine.value.filter(o => o.status === 'picked_up').length)

  async function loadAll () {
    if (!a.token) return
    loading.value = true
    try {
      const [av, mn, pg] = await Promise.all([
        availableOrders(svc, a.token),
        myDeliveries(svc, a.token),
        dispatchPings(svc, a.token),
      ])
      available.value = av
      mine.value = mn
      pings.value = pg
      handleNewPings(pg)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  /** Detect pings that arrived since the last poll and actively notify. */
  function handleNewPings (list: CourierPing[]) {
    const fresh = list.filter(p => !seen.has(p.id))
    for (const p of list) seen.add(p.id)
    if (!primed) { primed = true; return } // don't blast toasts for the backlog
    if (!fresh.length) return

    const first = fresh[0]
    snackMsg.value = fresh.length > 1
      ? `${fresh.length} new orders · next: head to ${first.delivery_address}`
      : `Order #${first.order_id} · head to ${first.delivery_address}`
    snackbar.value = true
    playChime()
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('🛵 New delivery', {
        body: `Order #${first.order_id} — start heading to ${first.delivery_address}`,
      })
    }
  }

  /** Short attention chime via WebAudio — no asset needed. */
  function playChime () {
    try {
      const Ctx = window.AudioContext || (window as any).webkitAudioContext
      if (!Ctx) return
      const ctx = new Ctx()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.type = 'sine'
      osc.frequency.setValueAtTime(880, ctx.currentTime)
      osc.frequency.setValueAtTime(1175, ctx.currentTime + 0.12)
      gain.gain.setValueAtTime(0.0001, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5)
      osc.start()
      osc.stop(ctx.currentTime + 0.52)
    } catch { /* audio not available — toast still shows */ }
  }

  async function accept (id: number) {
    if (!a.token) return
    try {
      await acceptOrder(svc, a.token, id)
      await loadAll()
    } catch (e: any) {
      error.value = e.message // 409 if another courier grabbed it first
    }
  }

  async function deliver (id: number) {
    if (!a.token) return
    try {
      await deliverOrder(svc, a.token, id)
      await loadAll()
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function dismissPing (id: number) {
    if (!a.token) return
    pings.value = pings.value.filter(p => p.id !== id) // optimistic
    try {
      await ackPing(svc, a.token, id)
    } catch (e: any) {
      error.value = e.message
    }
  }

  function logout () {
    doLogout(svc)
  }

  onMounted(async () => {
    // Ask once so we can raise an OS-level notification on new deliveries.
    if ('Notification' in window && Notification.permission === 'default') {
      try { await Notification.requestPermission() } catch { /* ignored */ }
    }
    await loadMe(svc)
    await loadAll()
    timer = window.setInterval(loadAll, 4000)
  })
  onUnmounted(() => clearInterval(timer))
</script>
