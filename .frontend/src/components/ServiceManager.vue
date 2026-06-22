<template>
  <v-container max-width="1100" class="py-6">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h5 font-weight-medium">{{ service.label }}</h2>
      <v-chip
        :color="healthy === false ? 'error' : healthy ? 'success' : 'grey'"
        class="ml-3"
        size="small"
        variant="tonal"
      >
        {{ healthy === null ? 'checking…' : healthy ? 'online' : 'offline' }}
      </v-chip>
      <v-spacer />
      <v-btn
        class="mr-2"
        :loading="loading"
        icon="mdi-refresh"
        variant="text"
        @click="load"
      />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">
        New {{ service.singular }}
      </v-btn>
    </div>

    <v-alert
      v-if="error"
      class="mb-4"
      closable
      type="error"
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>

    <v-data-table
      :headers="headers"
      :items="items"
      :loading="loading"
      item-value="id"
    >
      <template #item.is_active="{ value }">
        <v-chip :color="value ? 'success' : 'grey'" size="small" variant="tonal">
          {{ value ? 'active' : 'inactive' }}
        </v-chip>
      </template>
      <template #item.created_at="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #item.actions="{ item }">
        <v-btn
          color="error"
          icon="mdi-delete"
          size="small"
          variant="text"
          @click="remove(item)"
        />
      </template>
      <template #no-data>
        <div class="py-8 text-medium-emphasis">No {{ service.label.toLowerCase() }} yet.</div>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" max-width="500">
      <v-card :title="`New ${service.singular}`">
        <v-card-text>
          <v-text-field
            v-for="f in service.fields"
            :key="f.key"
            v-model="form[f.key]"
            class="mb-1"
            density="comfortable"
            :label="f.required ? `${f.label} *` : f.label"
            :type="f.type === 'password' ? 'password' : f.type === 'email' ? 'email' : 'text'"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :disabled="saving" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import {
    checkHealth,
    createRecord,
    deleteRecord,
    listRecords,
    type Record_,
  } from '@/api'
  import type { ServiceConfig } from '@/services'

  const props = defineProps<{ service: ServiceConfig }>()

  const items = ref<Record_[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const healthy = ref<boolean | null>(null)
  const dialog = ref(false)
  const form = ref<Record_>({})

  const headers = computed(() => [
    { title: 'ID', key: 'id' },
    ...props.service.fields
      .filter(f => f.type !== 'password')
      .map(f => ({ title: f.label, key: f.key })),
    { title: 'Active', key: 'is_active' },
    { title: 'Created', key: 'created_at' },
    { title: '', key: 'actions', sortable: false },
  ])

  async function load () {
    loading.value = true
    error.value = ''
    healthy.value = null
    try {
      items.value = await listRecords(props.service)
      healthy.value = true
    } catch (error_: any) {
      error.value = error_.message
      // Distinguish "service down" from "request failed" with a health ping.
      checkHealth(props.service)
        .then(() => (healthy.value = true))
        .catch(() => (healthy.value = false))
    } finally {
      loading.value = false
    }
  }

  function openCreate () {
    form.value = {}
    error.value = ''
    dialog.value = true
  }

  async function save () {
    saving.value = true
    error.value = ''
    try {
      await createRecord(props.service, form.value)
      dialog.value = false
      await load()
    } catch (error_: any) {
      error.value = error_.message
    } finally {
      saving.value = false
    }
  }

  async function remove (item: Record_) {
    error.value = ''
    try {
      await deleteRecord(props.service, item.id)
      await load()
    } catch (error_: any) {
      error.value = error_.message
    }
  }

  function formatDate (value: string) {
    return value ? new Date(value).toLocaleString() : ''
  }

  // Reload whenever the active service changes (tab switch).
  watch(() => props.service, load, { immediate: true })
</script>
