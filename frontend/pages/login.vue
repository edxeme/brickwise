<script setup lang="ts">
const { authenticate } = useAuth()

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const name = ref('')
const teamName = ref('')
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (mode.value === 'login') {
      await authenticate('login', { email: email.value, password: password.value })
    } else {
      await authenticate('register', {
        email: email.value,
        password: password.value,
        name: name.value,
        team_name: teamName.value,
      })
    }
    await navigateTo('/')
  } catch (e: unknown) {
    error.value =
      (e as { data?: { detail?: string }; message?: string }).data?.detail ??
      'No fue posible autenticar. Revisa los datos e inténtalo de nuevo.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-sm">
    <div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="mb-6 flex gap-2 text-sm">
        <button
          type="button"
          class="flex-1 rounded-lg px-3 py-2 font-medium"
          :class="mode === 'login' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'"
          @click="mode = 'login'"
        >
          Ingresar
        </button>
        <button
          type="button"
          class="flex-1 rounded-lg px-3 py-2 font-medium"
          :class="mode === 'register' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'"
          @click="mode = 'register'"
        >
          Registrarse
        </button>
      </div>

      <form class="space-y-3" @submit.prevent="submit">
        <template v-if="mode === 'register'">
          <input
            v-model="name"
            type="text"
            placeholder="Tu nombre"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <input
            v-model="teamName"
            type="text"
            placeholder="Nombre del equipo (p. ej. tu constructora)"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
        </template>
        <input
          v-model="email"
          type="email"
          placeholder="Correo"
          required
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Contraseña (mín. 8 caracteres)"
          required
          minlength="8"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
        />
        <p v-if="error" class="text-xs text-rose-600">{{ error }}</p>
        <button
          type="submit"
          :disabled="submitting"
          class="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {{ submitting ? 'Enviando…' : mode === 'login' ? 'Ingresar' : 'Crear cuenta y equipo' }}
        </button>
      </form>
    </div>
    <p class="mt-4 text-center text-xs text-slate-500">
      Al registrarte se crea tu equipo; los proyectos quedan limitados a él.
    </p>
  </div>
</template>
