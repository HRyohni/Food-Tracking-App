<template>
  <v-container class="py-12" max-width="460">
    <div class="text-center mb-6">
      <div class="wolt-tile wolt-tile--lg mx-auto mb-3">{{ role.emoji }}</div>
      <h1 class="wolt-section-title" style="font-size: 1.5rem">{{ role.title }}</h1>
      <div class="text-medium-emphasis">{{ role.subtitle }}</div>
    </div>

    <v-card elevation="2">
      <v-tabs v-model="mode" color="primary" grow>
        <v-tab value="login">Log in</v-tab>
        <v-tab value="register">Sign up</v-tab>
      </v-tabs>

      <v-card-text class="pt-5">
        <v-alert v-if="error" class="mb-4" closable type="error" variant="tonal" @click:close="error = ''">
          {{ error }}
        </v-alert>

        <!-- LOGIN -->
        <template v-if="mode === 'login'">
          <v-text-field
            v-model="email"
            class="mb-3"
            label="Email"
            prepend-inner-icon="mdi-email-outline"
            type="email"
          />
          <v-text-field
            v-model="password"
            label="Password"
            prepend-inner-icon="mdi-lock-outline"
            type="password"
            @keyup.enter="submitLogin"
          />
        </template>

        <!-- REGISTER -->
        <template v-else>
          <v-text-field
            v-for="f in svc.fields"
            :key="f.key"
            v-model="form[f.key]"
            class="mb-3"
            :label="f.required ? `${f.label} *` : f.label"
            :type="f.type === 'password' ? 'password' : f.type === 'email' ? 'email' : 'text'"
          />
        </template>
      </v-card-text>

      <v-card-actions class="px-4 pb-5">
        <v-btn
          v-if="mode === 'login'"
          block
          color="primary"
          :loading="busy"
          size="large"
          variant="flat"
          @click="submitLogin"
        >
          Log in
        </v-btn>
        <v-btn
          v-else
          block
          color="primary"
          :loading="busy"
          size="large"
          variant="flat"
          @click="submitRegister"
        >
          Create account &amp; continue
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, reactive, ref } from 'vue'
  import { createRecord, type Record_ } from '@/api'
  import { doLogin } from '@/auth'
  import { serviceByKey } from '@/services'

  const props = defineProps<{ serviceKey: string }>()
  const svc = serviceByKey(props.serviceKey)

  const ROLES: Record<string, { emoji: string, title: string, subtitle: string }> = {
    customer: { emoji: '🍔', title: 'Hungry?', subtitle: 'Log in to order from your favourite spots' },
    partner: { emoji: '🏪', title: 'Partner portal', subtitle: 'Manage your menu and incoming orders' },
    worker: { emoji: '🛵', title: 'Courier hub', subtitle: 'Pick up deliveries and earn on the road' },
  }
  const role = computed(() => ROLES[props.serviceKey] ?? { emoji: '🍽️', title: svc.singular, subtitle: '' })

  const mode = ref<'login' | 'register'>('login')
  const email = ref('')
  const password = ref('')
  const form = reactive<Record_>({})
  const busy = ref(false)
  const error = ref('')

  async function submitLogin () {
    busy.value = true
    error.value = ''
    try {
      await doLogin(svc, email.value, password.value)
    } catch (e: any) {
      error.value = e.message
    } finally {
      busy.value = false
    }
  }

  async function submitRegister () {
    busy.value = true
    error.value = ''
    try {
      await createRecord(svc, form)
      // Auto sign-in with the just-registered credentials.
      await doLogin(svc, form[svc.emailKey], form.password)
    } catch (e: any) {
      error.value = e.message
    } finally {
      busy.value = false
    }
  }
</script>
