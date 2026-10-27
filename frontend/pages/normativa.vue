<script setup lang="ts">
interface RegulationHit {
  documentTitle: string
  section: string | null
  content: string
  similarity: number
}

const SEARCH_QUERY = `
  query SearchRegulations($query: String!, $projectId: Int, $topK: Int) {
    searchRegulations(query: $query, projectId: $projectId, topK: $topK) {
      documentTitle
      section
      content
      similarity
    }
  }
`

const INGEST_MUTATION = `
  mutation IngestRegulation($documentTitle: String!, $content: String!, $section: String) {
    ingestRegulation(documentTitle: $documentTitle, content: $content, section: $section)
  }
`

const query = ref('')
const searching = ref(false)
const hits = ref<RegulationHit[] | null>(null)
const searched = ref(false)

async function search() {
  if (!query.value.trim()) return
  searching.value = true
  try {
    const response = await gql<{ data: { searchRegulations: RegulationHit[] } }>(SEARCH_QUERY, {
      query: query.value,
      topK: 5,
    })
    hits.value = response.data.searchRegulations
    searched.value = true
  } finally {
    searching.value = false
  }
}

const ingestForm = reactive({
  documentTitle: '',
  section: '',
  content: '',
})
const ingesting = ref(false)
const ingestMessage = ref('')

async function ingest() {
  if (!ingestForm.documentTitle || !ingestForm.content.trim()) return
  ingesting.value = true
  ingestMessage.value = ''
  try {
    const response = await gql<{ data: { ingestRegulation: number } }>(INGEST_MUTATION, {
      documentTitle: ingestForm.documentTitle,
      content: ingestForm.content,
      section: ingestForm.section || null,
    })
    ingestMessage.value = `Documento fragmentado e indexado: ${response.data.ingestRegulation} fragmentos.`
    ingestForm.documentTitle = ''
    ingestForm.section = ''
    ingestForm.content = ''
  } catch (e) {
    ingestMessage.value = `Error al ingestar: ${e}`
  } finally {
    ingesting.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight">Normativa</h1>
      <p class="mt-1 text-sm text-slate-600">
        Ingresa documentos normativos y consúltalos por similitud semántica (pgvector).
      </p>
    </div>

    <div class="grid gap-6 lg:grid-cols-2">
      <section>
        <form class="flex gap-2" @submit.prevent="search">
          <input
            v-model="query"
            type="text"
            placeholder="¿Qué norma buscas? p. ej. índice de construcción permitido"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <button
            type="submit"
            :disabled="searching"
            class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {{ searching ? 'Buscando…' : 'Buscar' }}
          </button>
        </form>

        <div v-if="searched" class="mt-6 space-y-4">
          <p v-if="!hits?.length" class="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
            Sin resultados. Ingresa documentos primero.
          </p>
          <article
            v-for="(hit, index) in hits"
            :key="index"
            class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div class="mb-2 flex items-center justify-between gap-4">
              <h2 class="text-sm font-semibold">{{ hit.documentTitle }}</h2>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs tabular-nums text-slate-600">
                {{ (hit.similarity * 100).toFixed(1) }}% afinidad
              </span>
            </div>
            <p v-if="hit.section" class="text-xs text-slate-500">{{ hit.section }}</p>
            <p class="mt-2 text-sm leading-relaxed text-slate-700">{{ hit.content }}</p>
          </article>
        </div>
      </section>

      <aside class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="mb-4 font-semibold">Ingestar documento</h2>
        <form class="space-y-3" @submit.prevent="ingest">
          <input
            v-model="ingestForm.documentTitle"
            type="text"
            placeholder="Título del documento (p. ej. POT Capítulo 4)"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <input
            v-model="ingestForm.section"
            type="text"
            placeholder="Sección (opcional)"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <textarea
            v-model="ingestForm.content"
            rows="8"
            placeholder="Pega el texto normativo aquí…"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
          <p v-if="ingestMessage" class="text-xs text-slate-600">{{ ingestMessage }}</p>
          <button
            type="submit"
            :disabled="ingesting"
            class="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {{ ingesting ? 'Indexando…' : 'Indexar documento' }}
          </button>
        </form>
      </aside>
    </div>
  </div>
</template>
