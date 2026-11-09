# Arquitetura — FazOEco

## Visão geral

O FazOEco é um portal automatizado de ofertas e afiliados composto por:

| Camada | Tecnologia | Responsabilidade |
|--------|------------|------------------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind | UI pública, SEO, painel admin |
| Backend | FastAPI + SQLAlchemy 2 (async) + Alembic | API REST, regras de negócio, jobs |
| Banco | PostgreSQL 16 | Persistência transacional |
| Orquestração | Docker Compose (+ Nginx em produção) | Rede, volumes, reverse proxy |

```text
Browser → Nginx (TLS) → Frontend (standalone) ─┐
                      └→ Backend (uvicorn) ─────┼→ PostgreSQL
                                                └→ Conectores (Amazon / ML / Shopee)
```

## Domínio

- **users** — administradores (JWT)
- **categories / products / offers** — catálogo e ofertas de afiliados
- **price_history** — histórico para gráficos e revalidação
- **logs / settings** — auditoria operacional e pesos/faixas configuráveis

Timestamps são gravados em **UTC** e convertidos para `America/Sao_Paulo` na leitura.

## Serviços de negócio

1. **PricingService** — desconto `Decimal` (HALF_UP), faixas dinâmicas, critérios de publicação  
2. **RankingService** — score 0–100 em 5 pilares com redistribuição transparente  
3. **DeduplicationService** — match por GTIN/EAN e chave loja+ID externo  
4. **http_client (SSRF-safe)** — allowlist de hosts de marketplace/API  

## Jobs (APScheduler)

- Ingestão periódica via conectores (simulação ou APIs reais)
- Revalidação de preço/disponibilidade e expiração automática
- Triggers manuais em `/api/v1/admin/jobs/*` e `/api/v1/jobs/*`

## SEO (frontend)

- `generateMetadata` dinâmico
- JSON-LD `Product` + `AggregateOffer` + `BreadcrumbList`
- `sitemap.ts` / `robots.ts`
- Ofertas expiradas permanecem indexáveis com alternativas da categoria

## Segurança (camadas)

1. CORS restrito (`BACKEND_CORS_ORIGINS`)
2. Security headers HTTP (middleware FastAPI)
3. Rate limit em login e busca pública
4. SSRF allowlist nas saídas HTTP dos conectores
5. Nginx TLS + rate zones em produção
