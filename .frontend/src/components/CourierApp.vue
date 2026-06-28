<template>
  <LoginCard v-if="!a.token" service-key="worker" />

  <v-container v-else class="py-6" max-width="900">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h5 font-weight-medium">Courier · {{ a.user?.name ?? '' }}</h2>
      <v-spacer />
      <v-btn prepend-icon="mdi-logout" variant="text" @click="logout">Log out</v-btn>
    </div>

    <v-alert v-if="error" class="mb-4" closable type="error" @click:close="error = ''">
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
      <span class="font-weight-medium">Order #{{ p.order_id }} accepted</span> — start heading to {{ p.delivery_address }}.
    </v-alert>

    <v-row>
      <!-- Available pool -->
      <v-col cols="12" md="6">
        <div class="d-flex align-center mb-2">
          <h3 class="text-h6">Available</h3>
          <v-spacer />
          <v-btn icon="mdi-refresh" :loading="loading" size="small" variant="text" @click="loadAll" />
        </div>
        <v-card v-for="o in available" :key="o.id" class="mb-2" variant="outlined">
          <v-card-text>
            <div class="d-flex align-center">
              <span class="font-weight-medium">Order #{{ o.id }}</span>
              <v-spacer />
              <span class="font-weight-medium">${{ o.total_amount.toFixed(2) }}</span>
            </div>
            <div class="text-caption text-medium-emphasis mt-1">
              {{ o.items.reduce((n, i) => n + i.quantity, 0) }} item(s) · to {{ o.delivery_address }}
            </div>
            <v-btn class="mt-2" color="primary" size="small" variant="tonal" @click="accept(o.id)">
              Accept delivery
            </v-btn>
          </v-card-text>
        </v-card>
        <div v-if="!available.length" class="text-medium-emphasis py-6 text-center">
          No orders ready for pickup.
        </div>
      </v-col>

      <!-- My deliveries -->
      <v-col cols="12" md="6">
        <h3 class="text-h6 mb-2">My deliveries</h3>
        <v-card v-for="o in mine" :key="o.id" class="mb-2" variant="outlined">
          <v-card-text>
            <div class="d-flex align-center">
              <span class="font-weight-medium">Order #{{ o.id }}</span>
              <v-chip class="ml-2" :color="statusColor(o.status)" size="small" variant="flat">
                {{ statusLabel(o.status) }}
              </v-chip>
              <v-spacer />
              <span class="font-weight-medium">${{ o.total_amount.toFixed(2) }}</span>
            </div>
            <div class="text-caption text-medium-emphasis mt-1">to {{ o.delivery_address }}</div>
            <v-btn
              v-if="o.status === 'picked_up'"
              class="mt-2"
              color="success"
              size="small"
              variant="tonal"
              @click="deliver(o.id)"
            >
              Mark delivered
            </v-btn>
          </v-card-text>
        </v-card>
        <div v-if="!mine.length" class="text-medium-emphasis py-6 text-center">
          No active deliveries.
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { onMounted, onUnmounted, ref } from 'vue'
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
  let timer: number | undefined

  async function loadAll () {
    if (!a.token) return
    loading.value = true
    try {
      [available.value, mine.value, pings.value] = await Promise.all([
        availableOrders(svc, a.token),
        myDeliveries(svc, a.token),
        dispatchPings(svc, a.token),
      ])
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
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
    await loadMe(svc)
    await loadAll()
    timer = window.setInterval(loadAll, 4000)
  })
  onUnmounted(() => clearInterval(timer))
</script>
