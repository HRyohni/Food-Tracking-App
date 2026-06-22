<template>
  <v-container class="py-10" max-width="460">
    <v-card>
      <v-tabs v-model="mode" color="primary" grow>
        <v-tab value="login">Log in</v-tab>
        <v-tab value="register">Register</v-tab>
      </v-tabs>

      <v-card-text>
        <v-alert v-if="error" class="mb-4" closable type="error" @click:close="error = ''">
          {{ error }}
        </v-alert>

        <!-- LOGIN -->
        <template v-if="mode === 'login'">
          <v-text-field
            v-model="email"
            class="mb-2"
            density="comfortable"
            label="Email"
            type="email"
          />
          <v-text-field
            v-model="password"
            density="comfortable"
            label="Password"
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
            class="mb-1"
            density="comfortable"
            :label="f.required ? `${f.label} *` : f.label"
            :type="f.type === 'password' ? 'password' : f.type === 'email' ? 'email' : 'text'"
          />
        </template>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn
          v-if="mode === 'login'"
          color="primary"
          :loading="busy"
          variant="flat"
          @click="submitLogin"
        >
          Log in
        </v-btn>
        <v-btn
          v-else
          color="primary"
          :loading="busy"
          variant="flat"
          @click="submitRegister"
        >
          Create account &amp; sign in
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
  import { reactive, ref } from 'vue'
  import { createRecord, type Record_ } from '@/api'
  import { doLogin } from '@/auth'
  import { serviceByKey } from '@/services'

  const props = defineProps<{ serviceKey: string }>()
  const svc = serviceByKey(props.serviceKey)

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
