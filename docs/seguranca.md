# Segurança

## Controles no backend

### 1. Autenticação

- Login OAuth2 password (`POST /api/v1/auth/login`)
- Senhas com `pwdlib` (Argon2)
- JWT HS256 (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Rotas `/api/v1/admin/*` exigem usuário ativo + `is_superuser`
- O login também grava o JWT em cookie `HttpOnly` (`fazoeeco_admin_token`). O painel não guarda o token no `localStorage`. Clientes de API continuam podendo usar `Authorization: Bearer`.

### 2. Rate limiting

Middleware `RateLimitMiddleware` (`app.core.security`):

| Escopo | Rota | Padrão |
|--------|------|--------|
| login | `POST /api/v1/auth/login` | `10/minute` |
| search | `GET /api/v1/offers` | `120/minute` |

Variáveis: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_LOGIN`, `RATE_LIMIT_SEARCH`, `REDIS_URL`.

Com `REDIS_URL`, o contador é compartilhado entre workers. Sem Redis, cada processo usa memória local. O Nginx reforça com `limit_req` (ver `infra/nginx.conf`).

### 3. Security headers

`SecurityHeadersMiddleware` adiciona:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy` (API: default-src none)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Cache-Control: no-store` em `/api/*`

### 4. CORS restrito

Apenas origens em `BACKEND_CORS_ORIGINS` (CSV). Sem `*`. Métodos e headers limitados.

### 5. SSRF

`app.services.http_client.SafeAsyncClient` / `assert_url_safe`:

- Allowlist de hosts Amazon / Mercado Livre / Shopee
- Bloqueio de redes privadas e metadata cloud
- Sem follow de redirects

### 6. Superfície de docs

Em `APP_ENV=production`, `/docs`, `/redoc` e `/openapi.json` ficam desabilitados.

## Checklist operacional

- [ ] Trocar `SECRET_KEY` por valor longo e aleatório
- [ ] Trocar senha `ADMIN_INITIAL_PASSWORD` no primeiro login
- [ ] Definir `BACKEND_CORS_ORIGINS` apenas com o domínio HTTPS público
- [ ] `DEBUG=false` e `ENABLE_SIMULATION_MODE=false` em produção
- [ ] TLS via Certbot + HSTS no Nginx
- [ ] Backups regulares do volume PostgreSQL
