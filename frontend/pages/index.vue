<script setup lang="ts">
type Rating = 'VIABLE' | 'CONDICIONES' | 'NO_VIABLE'

interface FeasibilitySummary {
  score: number
  rating: Rating
}

interface ProjectRow {
  id: number
  name: string
  location: string
  typology: string
  areaM2: number
  budgetCop: number
  feasibility: FeasibilitySummary
  criteria: { id: number }[]
}

const PROJECTS_QUERY = `
  query {
    projects {
      id
      name
      location
      typology
      areaM2
      budgetCop
      feasibility { score rating }
      criteria { id }
    }
  }
`

const {
  data: projects,
  refresh,
  pending,
} = await useAsyncData('projects', async () => {
  const response = await gql<{ data: { projects: ProjectRow[] } }>(PROJECTS_QUERY)
  return response.data.projects
})

const CREATE_MUTATION = `
  mutation CreateProject($input: CreateProjectInput!) {
    createProject(input: $input) { id }
  }
`

const emptyForm = () => ({
  name: '',
  location: '',
  typology: 'VIVIENDA',
  areaM2: 1000,
  budgetCop: 5_000_000_000,
})

const form = reactive(emptyForm())
const creating = ref(false)
const error = ref('')

async function createProject() {
  if (!form.name || !form.location) {
    error.value = 'Nombre y ubicación son obligatorios.'
    return
  }
  creating.value = true
  error.value = ''
  try {
    await gql(CREATE_MUTATION, {
      input: {
        ...form,
        areaM2: Number(form.areaM2),
        budgetCop: Number(form.budgetCop),
      },
    })
    Object.assign(form, emptyForm())
    await refresh()
  } catch (e) {
    error.value = `No se pudo crear el proyecto: ${e}`
  } finally {
    creating.value = false
  }
}

const ratingBadge: Record<Rating, string> = {
  VIABLE: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  CONDICIONES: 'bg-amber-100 text-amber-800 ring-amber-200',
  NO_VIABLE: 'bg-rose-100 text-rose-800 ring-rose-200',
}

const ratingLabel: Record<Rating, string> = {
  VIABLE: 'Viable',
  CONDICIONES: 'Con condiciones',
  NO_VIABLE: 'No viable',
}

function formatCop(value: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value)
}
</script>

<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight">Proyectos</h1>
      <p class="mt-1 text-sm text-slate-600">
        Evalúa la factibilidad de un proyecto con criterios ponderados: técnico, normativa, económico y de mercado.
      </p>
    </div>

    <div v-if="pending" class="text-slate-500">Cargando proyectos…</div>

    <div v-else class="grid gap-6 lg:grid-cols-3">
      <section class="lg:col-span-2">
        <p v-if="!projects?.length" class="rounded-lg border border-dashed border-slate-300 p-8 text-center text-slate-500">
          Aún no hay proyectos. Crea el primero con el formulario.
        </p>
        <ul v-else class="space-y-4">
          <li v-for="project in projects" :key="project.id">
            <NuxtLink
              :to="`/projects/${project.id}`"
              class="block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h2 class="font-semibold">{{ project.name }}</h2>
                  <p class="text-sm text-slate-600">
                    {{ project.location }} · {{ project.typology.toLowerCase() }} ·
                    {{ project.criteria.length }} criterios
                  </p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ project.areaM2.toLocaleString('es-CO') }} m² · {{ formatCop(project.budgetCop) }}
                  </p>
                </div>
                <div class="text-right">
                  <span
                    class="inline-block rounded-full px-3 py-1 text-xs font-medium ring-1"
                    :class="ratingBadge[project.feasibility.rating]"
                  >
                    {{ ratingLabel[project.feasibility.rating] }}
                  </span>
                  <p class="mt-2 text-2xl font-bold tabular-nums">
                    {{ project.feasibility.score.toFixed(1) }}
                  </p>
                </div>
              </div>
            </NuxtLink>
          </li>
        </ul>
      </section>

      <aside class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="mb-4 font-semibold">Nuevo proyecto</h2>
        <form class="space-y-3" @submit.prevent="createProject">
          <input
            v-model="form.name"
            type="text"
            placeholder="Nombre del proyecto"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <input
            v-model="form.location"
            type="text"
            placeholder="Ubicación (ciudad, barrio)"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <select
            v-model="form.typology"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          >
            <option value="VIVIENDA">Vivienda</option>
            <option value="COMERCIO">Comercio</option>
            <option value="INDUSTRIA">Industria</option>
            <option value="MIXTO">Mixto</option>
            <option value="INSTITUCIONAL">Institucional</option>
          </select>
          <label class="block text-xs text-slate-600">
            Área (m²)
            <input
              v-model.number="form.areaM2"
              type="number"
              min="1"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
            />
          </label>
          <label class="block text-xs text-slate-600">
            Presupuesto (COP)
            <input
              v-model.number="form.budgetCop"
              type="number"
              min="0"
              class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
            />
          </label>
          <p v-if="error" class="text-xs text-rose-600">{{ error }}</p>
          <button
            type="submit"
            :disabled="creating"
            class="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {{ creating ? 'Creando…' : 'Crear proyecto' }}
          </button>
        </form>
      </aside>
    </div>
  </div>
</template>
