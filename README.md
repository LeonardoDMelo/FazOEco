# FazOEco — Portal Automatizado de Ofertas e Afiliados

Stack: **Next.js 14+ (App Router)** · **FastAPI** · **PostgreSQL 16** · **Docker Compose**

## Estrutura

```text
.
├── .env.example          # Modelo de variáveis de ambiente
├── compose.yaml          # Orquestração (db, backend, frontend)
├── backend/              # API FastAPI + SQLAlchemy async + Alembic
├── frontend/             # Next.js (TypeScript + Tailwind CSS)
├── infra/                # Infraestrutura / scripts auxiliares
└── docs/                 # Documentação do projeto
```

## Pré-requisitos

- Docker e Docker Compose
- (Opcional, desenvolvimento local) Node.js 20+ e Python 3.12+

## Configuração rápida

```bash
# 1. Variáveis de ambiente
cp .env.example .env

# 2. Subir a stack
docker compose up --build
```

Serviços:

| Serviço   | URL                     |
|-----------|-------------------------|
| Frontend  | http://localhost:3000   |
| Backend   | http://localhost:8000   |
| API docs  | http://localhost:8000/docs |
| PostgreSQL| localhost:5432          |

## Backend (local, sem Docker)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Migrações (Alembic async)

```bash
cd backend
alembic revision --autogenerate -m "descricao"
alembic upgrade head
```

## Frontend (local, sem Docker)

```bash
cd frontend
npm install
npm run dev
```

## Fase atual

**Fase 1** — Estrutura base, configuração do ambiente e banco de dados.
