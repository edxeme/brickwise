# 🧱 Brickwise

**Evaluación de factibilidad de proyectos de construcción** — del lote al semáforo de viabilidad en minutos.

![CI](https://github.com/edxeme/brickwise/actions/workflows/ci.yml/badge.svg)

Veinte años de obra dejan una intuición: un proyecto no falla por una sola razón, falla por acumulación de supuestos sin verificar. Brickwise convierte esa intuición en modelo: criterios ponderados por categoría, semáforo de viabilidad y búsqueda semántica sobre la normativa que aplica a tu lote.

## Funcionalidades

- **Proyectos** con tipología (vivienda, comercio, industria, mixto, institucional), área y presupuesto en COP.
- **Criterios ponderados** en cuatro categorías — técnica, normativa, económica y de mercado — con peso 1–5 y calificación 0–100.
- **Semáforo de viabilidad**: score global = Σ(calificación · peso) / Σpeso → ≥ 80 viable · 60–79 con condiciones · < 60 no viable.
- **Riesgos críticos**: alerta cuando un criterio de peso ≥ 4 queda por debajo de 50.
- **Normativa vectorizada**: ingesta de documentos por fragmentos y búsqueda por similitud de coseno con embeddings locales (Ollama) o deterministas para desarrollo y pruebas.

## Arquitectura

| Capa | Herramientas |
| :--- | :--- |
| API | FastAPI · Strawberry GraphQL · SQLAlchemy 2.0 |
| Datos | PostgreSQL 16 · pgvector |
| Frontend | Nuxt 3 · TailwindCSS |
| Embeddings | Ollama (`nomic-embed-text`, opcional) |
| CI | GitHub Actions |

El backend expone `/graphql` (GraphiQL incluido) y `/health`. Sin Alembic por ahora: el `lifespan` de FastAPI crea la extensión `vector` y las tablas al arranque.

## Puesta en marcha

```bash
# 1) Base de datos
docker compose up -d db

# 2) Backend (FastAPI en :8000)
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload --port 8000

# 3) Frontend (Nuxt en :3000)
cd ../frontend
npm install
npm run dev
```

Con Ollama instalado, activa embeddings semánticos reales:

```bash
ollama pull nomic-embed-text
BRICKWISE_EMBEDDER=ollama uvicorn app.main:app --reload --port 8000
```

Variables de entorno: `DATABASE_URL`, `BRICKWISE_EMBEDDER` (`hash` | `ollama`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `BRICKWISE_ALLOWED_ORIGINS`.

## Pruebas

```bash
cd backend && .venv/bin/pytest -q
```

## Roadmap

- Migraciones con Alembic
- Autenticación y equipos
- Comparación de alternativas de emplazamiento
- Mapa interactivo con retiros normativos
- Exportación de informes de factibilidad

## Licencia

MIT
