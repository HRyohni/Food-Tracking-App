<template>
  <v-app>
    <v-app-bar color="primary" flat>
      <v-app-bar-title>Food Tracking — Admin</v-app-bar-title>
      <v-spacer />
      <v-btn icon="mdi-theme-light-dark" @click="theme.cycle()" />
    </v-app-bar>

    <v-main>
      <v-tabs v-model="tab" align-tabs="center" color="primary" grow>
        <v-tab
          v-for="s in services"
          :key="s.key"
          :prepend-icon="s.icon"
          :value="s.key"
        >
          {{ s.label }}
        </v-tab>
      </v-tabs>

      <ServiceManager :service="active" />
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
  import { computed, ref } from 'vue'
  import { useTheme } from 'vuetify'
  import ServiceManager from '@/components/ServiceManager.vue'
  import { services } from '@/services'

  const theme = useTheme()
  const tab = ref(services[0].key)
  const active = computed(() => services.find(s => s.key === tab.value) ?? services[0])
</script>
