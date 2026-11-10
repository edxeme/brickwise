<script setup lang="ts">
type Rating = 'VIABLE' | 'CONDICIONES' | 'NO_VIABLE'

interface CategoryScore {
  category: string
  score: number
}

interface Criterion {
  id: number
  category: string
  name: string
  weight: number
  score: number
  notes: string | null
  alternativeId: number | null
}

interface FeasibilitySummary {
  score: number
  rating: Rating
  byCategory: CategoryScore[]
  criticalFlags: string[]
}

interface SiteAlternative {
  id: number
  name: string
  notes: string | null
  criteria: Criterion[]
  feasibility: FeasibilitySummary
}

interface Project {
  id: number
  name: string
  location: string
  typology: string
  areaM2: number
  budgetCop: number
  criteria: Criterion[]
  alternatives: SiteAlternative[]
  feasibility: FeasibilitySummary
}

const route = useRoute()
const projectId = Number(route.params.id)

const PROJECT_QUERY = `
  query Project($id: Int!) {
    project(id: $id) {
      id
      name
      location
      typology
      areaM2
      budgetCop
      criteria { id category name weight score notes alternativeId }
      alternatives { id name notes criteria { id } feasibility { score rating } }
      feasibility { score rating byCategory { category score } criticalFlags }
    }
  }
`

const {
  data: project,
  refresh,
  pending,
} = await useAsyncData(`project-${projectId}`, async () => {
  const response = await gql<{ data: { project: Project | null } }>(PROJECT_QUERY, {
    id: projectId,
  })
  return response.data.project
})

const UPDATE_MUTATION = `
  mutation UpdateCriterion($id: Int!, $weight: Int, $score: Float) {
    updateCriterion(id: $id, weight: $weight, score: $score) { id }
  }
`

const ADD_MUTATION = `
  mutation AddCriterion($projectId: Int!, $input: CriterionInput!) {
    addCriterion(projectId: $projectId, input: $input) { id }
  }
`

const CREATE_ALTERNATIVE_MUTATION = `
  mutation CreateAlternative($input: CreateAlternativeInput!) {
    createAlternative(input: $input) { id }
  }
`

const ADD_ALT_CRITERION_MUTATION = `
  mutation AddAlternativeCriterion($alternativeId: Int!, $input: CriterionInput!) {
    addAlternativeCriterion(alternativeId: $alternativeId, input: $input) { id }
  }
`

async function saveCriterion(criterion: Criterion) {
  await gql(UPDATE_MUTATION, {
    id: criterion.id,
    weight: criterion.weight,
    score: criterion.score,
  })
  await refresh()
}

const newCriterion = reactive({
  name: '',
  category: 'TECNICA',
  weight: 3,
  score: 70,
})
const adding = ref(false)

async function addCriterion() {
  if (!newCriterion.name) return
  adding.value = true
  try {
    await gql(ADD_MUTATION, {
      projectId,
      input: { ...newCriterion, weight: Number(newCriterion.weight), score: Number(newCriterion.score) },
    })
    newCriterion.name = ''
    newCriterion.score = 70
    await refresh()
  } finally {
    adding.value = false
  }
}

const alternativeName = ref('')
const creatingAlternative = ref(false)

async function createAlternative() {
  if (!alternativeName.value) return
  creatingAlternative.value = true
  try {
    await gql(CREATE_ALTERNATIVE_MUTATION, {
      input: { projectId, name: alternativeName.value },
    })
    alternativeName.value = ''
    await refresh()
  } finally {
    creatingAlternative.value = false
  }
}

const alternativeCriterion = reactive({
  alternativeId: null as number | null,
  name: '',
  category: 'TECNICA',
  weight: 3,
  score: 70,
})

async function addAlternativeCriterion() {
  if (!alternativeCriterion.alternativeId || !alternativeCriterion.name) return
  try {
    await gql(ADD_ALT_CRITERION_MUTATION, {
      alternativeId: alternativeCriterion.alternativeId,
      input: {
        name: alternativeCriterion.name,
        category: alternativeCriterion.category,
        weight: Number(alternativeCriterion.weight),
        score: Number(alternativeCriterion.score),
      },
    })
    alternativeCriterion.name = ''
    alternativeCriterion.score = 70
    await refresh()
  } finally {
    creatingAlternative.value = false
  }
}

async function downloadReport() {
  const token = useCookie<string | null>('brickwise_token')
  const response = await $fetch<Blob>(
    `${apiRoot()}/projects/${projectId}/report.md`,
    { headers: token.value ? { Authorization: `Bearer ${token.value}` } : {} },
  )
  const url = URL.createObjectURL(response)
  const link = document.createElement('a')
  link.href = url
  link.download = `informe-factibilidad-${projectId}.md`
  link.click()
  URL.revokeObjectURL(url)
}

const ratingBadge: Record<Rating, string> = {
  VIABLE: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  CONDICIONES: 'bg-amber-100 text-amber-800 ring-amber-200',
  NO_VIABLE: 'bg-rose-100 text-rose-800 ring-rose-200',
}

const ratingLabel: Record<Rating, string> = {
  VIABLE: 'Viable',
  CONDICIONES: 'Viable con condiciones',
  NO_VIABLE: 'No viable',
}

const categoryLabel: Record<string, string> = {
  tecnica: 'Técnica',
  normativa: 'Normativa',
  economica: 'Económica',
  mercado: 'Mercado',
}
</script>

<template>
  <div>
    <p v-if="pending" class="text-slate-500">Cargando proyecto…</p>
    <p v-else-if="!project" class="text-slate-500">Proyecto no encontrado.</p>

    <template v-else>
      <div class="mb-8 flex items-start justify-between gap-6">
        <div>
          <NuxtLink to="/" class="text-xs text-slate-500 hover:text-slate-900">← Proyectos</NuxtLink>
          <h1 class="mt-1 text-2xl font-bold tracking-tight">{{ project.name }}</h1>
          <p class="text-sm text-slate-600">
            {{ project.location }} · {{ project.typology.toLowerCase() }} ·
            {{ project.areaM2.toLocaleString('es-CO') }} m²
          </p>
        </div>
        <div class="flex flex-col items-end gap-2">
          <div class="rounded-xl border border-slate-200 bg-white px-6 py-4 text-center shadow-sm">
            <span
              class="inline-block rounded-full px-3 py-1 text-xs font-medium ring-1"
              :class="ratingBadge[project.feasibility.rating]"
            >
              {{ ratingLabel[project.feasibility.rating] }}
            </span>
            <p class="mt-2 text-4xl font-bold tabular-nums">{{ project.feasibility.score.toFixed(1) }}</p>
          </div>
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium hover:border-slate-400"
            @click="downloadReport"
          >
            ⬇ Descargar informe
          </button>
        </div>
      </div>

      <div v-if="project.feasibility.criticalFlags.length" class="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
        <strong class="font-semibold">Riesgos críticos:</strong>
        {{ project.feasibility.criticalFlags.join(', ') }} — peso alto con calificación baja.
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <section class="lg:col-span-2">
          <h2 class="mb-3 font-semibold">Criterios</h2>
          <ul class="space-y-3">
            <li
              v-for="criterion in project.criteria.filter((c) => !c.alternativeId)"
              :key="criterion.id"
              class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="font-medium">{{ criterion.name }}</p>
                  <p class="text-xs text-slate-500">
                    {{ categoryLabel[criterion.category] ?? criterion.category }}
                  </p>
                </div>
                <div class="flex items-center gap-4">
                  <label class="text-xs text-slate-600">
                    Peso
                    <select
                      v-model.number="criterion.weight"
                      class="ml-1 rounded border border-slate-300 bg-white px-2 py-1 text-sm"
                      @change="saveCriterion(criterion)"
                    >
                      <option v-for="w in 5" :key="w" :value="w">{{ w }}</option>
                    </select>
                  </label>
                  <label class="text-xs text-slate-600">
                    Calificación
                    <input
                      v-model.number="criterion.score"
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      class="ml-2 w-36 align-middle"
                      @change="saveCriterion(criterion)"
                    />
                    <span class="ml-2 w-10 tabular-nums text-sm font-semibold">{{ criterion.score }}</span>
                  </label>
                </div>
              </div>
            </li>
          </ul>

          <form class="mt-4 flex flex-wrap items-center gap-2" @submit.prevent="addCriterion">
            <input
              v-model="newCriterion.name"
              type="text"
              placeholder="Nuevo criterio (p. ej. disponibilidad de redes)"
              class="min-w-56 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
            />
            <select
              v-model="newCriterion.category"
              class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="TECNICA">Técnica</option>
              <option value="NORMATIVA">Normativa</option>
              <option value="ECONOMICA">Económica</option>
              <option value="MERCADO">Mercado</option>
            </select>
            <select v-model.number="newCriterion.weight" class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
              <option v-for="w in 5" :key="w" :value="w">Peso {{ w }}</option>
            </select>
            <input
              v-model.number="newCriterion.score"
              type="number"
              min="0"
              max="100"
              class="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              :disabled="adding"
              class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              Añadir
            </button>
          </form>

          <section class="mt-10">
            <h2 class="mb-3 font-semibold">Alternativas de emplazamiento</h2>
            <p v-if="!project.alternatives.length" class="text-sm text-slate-500">
              Registra lotes alternativos con criterios propios y compáralos contra el proyecto principal.
            </p>
            <ul v-else class="space-y-3">
              <li
                v-for="alternative in [...project.alternatives].sort((a, b) => b.feasibility.score - a.feasibility.score)"
                :key="alternative.id"
                class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div class="flex items-center justify-between gap-4">
                  <div>
                    <p class="font-medium">{{ alternative.name }}</p>
                    <p class="text-xs text-slate-500">{{ alternative.criteria.length }} criterios</p>
                  </div>
                  <div class="text-right">
                    <span
                      class="inline-block rounded-full px-3 py-1 text-xs font-medium ring-1"
                      :class="ratingBadge[alternative.feasibility.rating]"
                    >
                      {{ ratingLabel[alternative.feasibility.rating] }}
                    </span>
                    <p class="mt-1 text-2xl font-bold tabular-nums">
                      {{ alternative.feasibility.score.toFixed(1) }}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  class="mt-3 text-xs text-slate-600 hover:text-slate-900"
                  @click="alternativeCriterion.alternativeId = alternative.id"
                >
                  + añadir criterio a esta alternativa
                </button>
              </li>
            </ul>

            <div class="mt-4 flex flex-wrap items-center gap-2">
              <input
                v-model="alternativeName"
                type="text"
                placeholder="Nueva alternativa (p. ej. Lote vía Aguachica)"
                class="min-w-56 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
                @keyup.enter="createAlternative"
              />
              <button
                type="button"
                :disabled="creatingAlternative"
                class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
                @click="createAlternative"
              >
                Crear alternativa
              </button>
            </div>

            <form
              v-if="alternativeCriterion.alternativeId"
              class="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3"
              @submit.prevent="addAlternativeCriterion"
            >
              <span class="text-xs text-slate-500">Criterio para alternativa #{{ alternativeCriterion.alternativeId }}</span>
              <input
                v-model="alternativeCriterion.name"
                type="text"
                placeholder="Nombre del criterio"
                class="min-w-48 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <select v-model="alternativeCriterion.category" class="rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm">
                <option value="TECNICA">Técnica</option>
                <option value="NORMATIVA">Normativa</option>
                <option value="ECONOMICA">Económica</option>
                <option value="MERCADO">Mercado</option>
              </select>
              <select v-model.number="alternativeCriterion.weight" class="rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm">
                <option v-for="w in 5" :key="w" :value="w">Peso {{ w }}</option>
              </select>
              <input
                v-model.number="alternativeCriterion.score"
                type="number"
                min="0"
                max="100"
                class="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button type="submit" class="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white hover:bg-slate-700">
                Añadir
              </button>
              <button
                type="button"
                class="text-xs text-slate-500 hover:text-slate-900"
                @click="alternativeCriterion.alternativeId = null"
              >
                cancelar
              </button>
            </form>
          </section>
        </section>

        <aside class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 class="mb-4 font-semibold">Por categoría</h2>
          <p v-if="!project.feasibility.byCategory.length" class="text-sm text-slate-500">
            Añade criterios para ver el desglose.
          </p>
          <ul v-else class="space-y-4">
            <li v-for="category in project.feasibility.byCategory" :key="category.category">
              <div class="mb-1 flex justify-between text-sm">
                <span>{{ categoryLabel[category.category] ?? category.category }}</span>
                <span class="font-semibold tabular-nums">{{ category.score.toFixed(1) }}</span>
              </div>
              <div class="h-2 rounded-full bg-slate-100">
                <div
                  class="h-2 rounded-full"
                  :class="category.score >= 80 ? 'bg-emerald-500' : category.score >= 60 ? 'bg-amber-500' : 'bg-rose-500'"
                  :style="{ width: `${category.score}%` }"
                />
              </div>
            </li>
          </ul>
        </aside>
      </div>
    </template>
  </div>
</template>
