<script setup lang="ts">
/** Mapa de retiros: dibuja el lote, calcula el polígono edificable y lo muestra. */

interface SetbackPreview {
  valid: boolean
  message: string
  buildable: [number, number][]
  lotAreaM2: number
  buildableAreaM2: number
}

const mapContainer = ref<HTMLElement | null>(null)
const setback = ref(3)
const vertices = ref<[number, number][]>([])
const result = ref<SetbackPreview | null>(null)
const computing = ref(false)
const error = ref('')

let map: import('leaflet').Map | null = null
let lotLayer: import('leaflet').Layer | null = null
let buildableLayer: import('leaflet').Layer | null = null
type LeafletModule = typeof import('leaflet')

let leaflet: LeafletModule | null = null

onMounted(async () => {
  leaflet = await import('leaflet')
  map = leaflet.map(mapContainer.value!, { doubleClickZoom: false }).setView([4.65, -74.05], 17)
  leaflet
    .tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    })
    .addTo(map)

  map.on('click', (event: import('leaflet').LeafletMouseEvent) => {
    const point: [number, number] = [event.latlng.lat, event.latlng.lng]
    vertices.value = [...vertices.value, point]
    drawLot()
  })
})

function drawLot() {
  if (!map || !leaflet) return
  if (lotLayer) {
    map.removeLayer(lotLayer)
    lotLayer = null
  }
  if (vertices.value.length >= 3) {
    lotLayer = leaflet.polygon(vertices.value, {
      color: '#0f172a',
      weight: 2,
      fillOpacity: 0.1,
    }).addTo(map)
  }
  for (const [lat, lng] of vertices.value) {
    lotLayer = leaflet.circleMarker([lat, lng], {
      radius: 4,
      color: '#0f172a',
    }).addTo(map)
  }
}

function clearLot() {
  vertices.value = []
  result.value = null
  error.value = ''
  if (map && lotLayer) {
    map.removeLayer(lotLayer)
    lotLayer = null
  }
  if (map && buildableLayer) {
    map.removeLayer(buildableLayer)
    buildableLayer = null
  }
}

async function compute() {
  error.value = ''
  result.value = null
  if (vertices.value.length < 3) {
    error.value = 'Haz clic en el mapa para definir al menos 3 vértices del lote.'
    return
  }
  computing.value = true
  try {
    const token = useCookie<string | null>('brickwise_token')
    result.value = await $fetch<SetbackPreview>(`${apiRoot()}/setbacks/preview`, {
      method: 'POST',
      body: { coordinates: vertices.value, setback_m: Number(setback.value) },
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
    })
    drawBuildable()
  } catch (e: unknown) {
    error.value = 'No se pudo calcular el retiro. ¿Está corriendo el backend?'
  } finally {
    computing.value = false
  }
}

function drawBuildable() {
  if (!map || !leaflet || !result.value?.valid) return
  if (buildableLayer) {
    map.removeLayer(buildableLayer)
    buildableLayer = null
  }
  buildableLayer = leaflet.polygon(result.value.buildable, {
    color: '#059669',
    weight: 2,
    fillOpacity: 0.25,
  }).addTo(map)
  map.fitBounds(leaflet.polygon(result.value.buildable).getBounds(), { padding: [24, 24] })
}

const formatM2 = (value: number) =>
  `${value.toLocaleString('es-CO', { maximumFractionDigits: 1 })} m²`
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight">Mapa de retiros normativos</h1>
      <p class="mt-1 text-sm text-slate-600">
        Dibuja el lote haciendo clic sobre el mapa, define el retiro y visualiza el área edificable.
      </p>
    </div>

    <div class="grid gap-6 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <div ref="mapContainer" class="h-96 rounded-xl border border-slate-200 shadow-sm" />
      </div>

      <aside class="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div>
          <label class="text-xs text-slate-600">
            Retiro normativo: <strong>{{ setback }} m</strong>
            <input
              v-model.number="setback"
              type="range"
              min="0"
              max="15"
              step="0.5"
              class="mt-2 w-full"
            />
          </label>
        </div>

        <div class="flex gap-2">
          <button
            type="button"
            :disabled="computing"
            class="flex-1 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            @click="compute"
          >
            {{ computing ? 'Calculando…' : 'Calcular edificable' }}
          </button>
          <button
            type="button"
            class="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:border-slate-400"
            @click="clearLot"
          >
            Limpiar
          </button>
        </div>

        <p class="text-xs text-slate-500">
          Vértices del lote: <strong>{{ vertices.length }}</strong>
        </p>

        <p v-if="error" class="text-xs text-rose-600">{{ error }}</p>

        <div v-if="result" class="space-y-2 text-sm">
          <p
            v-if="!result.valid"
            class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800"
          >
            {{ result.message }}
          </p>
          <template v-else>
            <div class="flex justify-between">
              <span class="text-slate-600">Área del lote</span>
              <span class="font-semibold tabular-nums">{{ formatM2(result.lotAreaM2) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Área edificable</span>
              <span class="font-semibold tabular-nums text-emerald-700">
                {{ formatM2(result.buildableAreaM2) }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Perdido en retiros</span>
              <span class="font-semibold tabular-nums text-rose-600">
                {{ formatM2(result.lotAreaM2 - result.buildableAreaM2) }}
              </span>
            </div>
          </template>
        </div>
      </aside>
    </div>
  </div>
</template>
