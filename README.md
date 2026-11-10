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
| Datos | PostgreSQL 16 · pgvector · Alembic |
| Auth | JWT (PyJWT) · bcrypt, equipos con scoping de proyectos |
| Frontend | Nuxt 3 · TailwindCSS · Leaflet |
| Embeddings | Ollama (`nomic-embed-text`, opcional) |
| CI | GitHub Actions |

El backend expone `/graphql` (protegido con JWT), `/health`, `/auth/register`, `/auth/login`, `GET /projects/{id}/report.md` y `POST /setbacks/preview`. El `lifespan` de FastAPI crea la extensión `vector` y las tablas al arranque; el esquema también se gestiona con Alembic (`backend/alembic.ini`, migraciones en `backend/migrations`).

## Puesta en marcha

```bash
# 1) Base de datos
docker compose up -d db

# 2) Esquema con Alembic (o simplemente arranca el backend: create_all lo cubre)
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000

# 3) Frontend (Nuxt en :3000)
cd ../frontend
npm install
npm run dev
```

La primera vez, regístrate desde la interfaz: se crea tu equipo y los proyectos quedan limitados a él.

Con Ollama instalado, activa embeddings semánticos reales:

```bash
ollama pull nomic-embed-text
BRICKWISE_EMBEDDER=ollama uvicorn app.main:app --reload --port 8000
```

Variables de entorno: `DATABASE_URL`, `BRICKWISE_EMBEDDER` (`hash` | `ollama`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `BRICKWISE_ALLOWED_ORIGINS`, `BRICKWISE_SECRET_KEY` (firma de JWT; usa una clave de 32+ bytes en producción), `BRICKWISE_TOKEN_TTL_DAYS`.

## Pruebas

```bash
cd backend && .venv/bin/pytest -q
```

## Roadmap

- [x] Migraciones con Alembic
- [x] Autenticación y equipos
- [x] Comparación de alternativas de emplazamiento
- [x] Mapa interactivo con retiros normativos
- [x] Exportación de informes de factibilidad

## Próximos pasos

- Roles por equipo (propietario, analista, lectura)
- Retiros diferenciados por frente (frontal, lateral, posterior)
- Informes en PDF con la marca del equipo
- Geometrías de lote persistidas por alternativa

## Licencia

MIT
