# Integrações — Conectores de marketplace

## Modo simulação

`ENABLE_SIMULATION_MODE=true` (padrão em desenvolvimento) faz os conectores retornarem `mock_data` sem chamar APIs externas. Ideal para demos e CI.

## Conectores

| Conector | Base URL | Credenciais |
|----------|----------|-------------|
| Amazon | `https://webservices.amazon.com.br` | `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG` |
| Mercado Livre | `https://api.mercadolibre.com` | `MERCADOLIVRE_SITE_ID` (+ token/afiliado opcionais) |
| Shopee | `https://open-api.affiliate.shopee.com.br` | `SHOPEE_PARTNER_ID`, `SHOPEE_PARTNER_KEY`, `SHOPEE_SHOP_ID` |

Cada conector implementa `BaseConnector`:

- `has_credentials()` — decide se a chamada live é possível
- `_fetch_live()` / `_fetch_simulated()` — coleta ofertas
- `fetch_offers()` — isola falhas (um marketplace não derruba os outros)

## SSRF

Toda saída HTTP passa por `app.services.http_client.assert_url_safe`:

- Apenas HTTPS (HTTP só fora de produção/debug)
- Hostname na allowlist de marketplaces/APIs
- Bloqueio de IPs privados, loopback e metadata (`169.254.169.254`)
- Redirects desabilitados (`follow_redirects=False`)

Hosts extras: `SSRF_ALLOWED_HOSTS=host1,host2` no `.env`.

## Disparo manual

- Painel admin → Conectores → executar busca
- API: `POST /api/v1/admin/connectors/run` (JWT admin)
- Jobs: ingestão/revalidação via scheduler ou endpoints de jobs

## Normalização

Todas as respostas viram `NormalizedOffer` (preço, GTIN, rating, URL de afiliado, disponibilidade) antes de pricing, ranking e deduplicação.
