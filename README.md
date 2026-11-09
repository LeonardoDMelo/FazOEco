# Echonomiza — Portal Automatizado de Ofertas e Afiliados

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

## Documentação

| Guia | Arquivo |
|------|---------|
| Arquitetura | [docs/arquitetura.md](docs/arquitetura.md) |
| Instalação | [docs/instalacao.md](docs/instalacao.md) |
| Integrações | [docs/integracoes.md](docs/integracoes.md) |
| Afiliados | [docs/afiliados.md](docs/afiliados.md) |
| Segurança | [docs/seguranca.md](docs/seguranca.md) |
| Implantação VPS | [docs/implantacao.md](docs/implantacao.md) |

## Produção

```bash
docker compose -f infra/compose.prod.yaml --env-file .env.prod up -d --build
```

Imagens multi-stage: backend slim (`target: runtime`) e frontend Next.js `standalone` (~120MB).

## Fase atual

**Fase 10** — Segurança (SSRF, rate limit, headers), Docker de produção, suíte E2E (20 casos) e documentação.

### Admin

- UI: http://localhost:3000/admin/login
- Credenciais via `.env`: `ADMIN_INITIAL_EMAIL` / `ADMIN_INITIAL_PASSWORD` (seed automático no startup)
- Padrão local: `admin@fazoeeco.local` / `Admin123!`
- Endpoints: `/api/v1/admin/*` (JWT Bearer)

### Domínio (tabelas)

`users` · `categories` · `products` · `offers` · `price_history` · `logs` · `settings`

Timestamps persistem em **UTC**; schemas de leitura convertem para **America/Sao_Paulo**.

### Serviços de negócio

| Serviço | Responsabilidade |
|---------|------------------|
| `PricingService` | Desconto `Decimal`, faixas dinâmicas e critérios de publicação |
| `RankingService` | Score 0–100 em 5 pilares com redistribuição transparente |
| `DeduplicationService` | Match por GTIN/EAN e atualização de ofertas existentes |

```bash
docker compose exec backend pytest -q
```
