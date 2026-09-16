<template>
  <v-app>
    <v-app-bar color="surface" flat>
      <v-container class="d-flex align-center py-0" style="max-width: 1200px">
        <div class=" mt-10 wolt-logo">
          <span class="wolt-logo__mark">FTA</span>
          <span class="wolt-logo__text">Food Tracking app</span>
        </div>
        <v-spacer />
        <v-btn icon="mdi-theme-light-dark" variant="text" @click="theme.cycle()" />
      </v-container>
    </v-app-bar>

    <v-main class="wolt-main">
      <div class="wolt-nav">
        <v-container class="py-0" style="max-width: 1200px">
          <v-tabs v-model="tab" align-tabs="center" color="primary" density="comfortable" slider-color="primary">
            <v-tab prepend-icon="mdi-silverware-fork-knife" value="customer">Order food</v-tab>
            <v-tab prepend-icon="mdi-storefront" value="partner">Partner</v-tab>
            <v-tab prepend-icon="mdi-bike-fast" value="courier">Courier</v-tab>
            <v-tab prepend-icon="mdi-cog" value="admin">Admin</v-tab>
          </v-tabs>
        </v-container>
      </div>

      <CustomerApp v-if="tab === 'customer'" />
      <PartnerApp v-else-if="tab === 'partner'" />
      <CourierApp v-else-if="tab === 'courier'" />

      <template v-else>
        <v-container class="pt-4 pb-0" style="max-width: 1200px">
          <v-tabs v-model="adminTab" align-tabs="center" color="primary" density="compact">
            <v-tab v-for="s in services" :key="s.key" :prepend-icon="s.icon" :value="s.key">
              {{ s.label }}
            </v-tab>
          </v-tabs>
        </v-container>
        <ServiceManager :service="activeAdmin" />
      </template>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
  import { computed, ref } from 'vue'
  import { useTheme } from 'vuetify'
  import CourierApp from '@/components/CourierApp.vue'
  import CustomerApp from '@/components/CustomerApp.vue'
  import PartnerApp from '@/components/PartnerApp.vue'
  import ServiceManager from '@/components/ServiceManager.vue'
  import { services } from '@/services'

  const theme = useTheme()
  const tab = ref('customer')

  // Admin sub-tabs keep the original generic CRUD per service.
  const adminTab = ref(services[0].key)
  const activeAdmin = computed(() => services.find(s => s.key === adminTab.value) ?? services[0])
</script>
