# Instalação (desenvolvimento)

## Pré-requisitos

- Docker Desktop / Docker Engine + Compose v2
- (Opcional) Node.js 20+ e Python 3.12+ para rodar fora dos containers

## Setup rápido

```bash
cp .env.example .env
docker compose up --build
```

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend / Swagger | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### Admin local

- UI: http://localhost:3000/admin/login  
- Credenciais padrão (`.env`): `admin@fazoeeco.local` / `Admin123!`  
- Seed automático no startup via `ADMIN_INITIAL_*`

## Migrações

```bash
docker compose exec backend alembic upgrade head
# ou gerar revisão:
docker compose exec backend alembic revision --autogenerate -m "descricao"
```

## Testes

```bash
docker compose exec backend pip install -r requirements.txt   # se o container foi recriado sem deps
docker compose exec backend pytest -q
```

A suíte inclui unitários em `backend/app/tests/` e os **20 casos E2E** em `backend/tests/test_full_pipeline.py`.

## Frontend / Backend locais (sem Docker)

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Garanta que `DATABASE_URL` aponte para o Postgres acessível e que `NEXT_PUBLIC_API_URL` / `API_URL` estejam corretos.
