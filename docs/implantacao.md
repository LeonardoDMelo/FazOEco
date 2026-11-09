# Implantação em VPS (Linux + Docker + Nginx)

Alvo: VPS com **~2GB RAM**, Ubuntu 22.04/24.04.

## 1. Preparar o servidor

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER   # reabra a sessão SSH
```

Clone o repositório:

```bash
git clone https://github.com/LeonardoDMelo/FazOEco.git
cd FazOEco
```

## 2. Ambiente de produção

```bash
cp .env.example .env.prod
nano .env.prod
```

Ajustes mínimos:

```env
APP_ENV=production
DEBUG=false
SECRET_KEY=<gere-com-openssl-rand-hex-32>
POSTGRES_PASSWORD=<forte>
BACKEND_CORS_ORIGINS=https://SEU_DOMINIO
NEXT_PUBLIC_API_URL=https://SEU_DOMINIO
NEXT_PUBLIC_SITE_URL=https://SEU_DOMINIO
ADMIN_INITIAL_EMAIL=admin@SEU_DOMINIO
ADMIN_INITIAL_PASSWORD=<troque-no-primeiro-login>
ENABLE_SIMULATION_MODE=false
RATE_LIMIT_ENABLED=true
WEB_CONCURRENCY=2
```

Edite `infra/nginx.conf` e substitua `SEU_DOMINIO` pelo hostname real.

## 3. Certificado TLS (primeira emissão)

1. Temporariamente comente o bloco `listen 443` **ou** suba só HTTP para o challenge ACME.
2. Emita o certificado:

```bash
docker compose -f infra/compose.prod.yaml --env-file .env.prod run --rm certbot \
  certonly --webroot -w /var/www/certbot -d SEU_DOMINIO --email voce@SEU_DOMINIO --agree-tos --no-eff-email
```

3. Confirme os caminhos em `nginx.conf` e suba a stack completa:

```bash
docker compose -f infra/compose.prod.yaml --env-file .env.prod up -d --build
docker compose -f infra/compose.prod.yaml --env-file .env.prod exec backend alembic upgrade head
```

## 4. Imagens otimizadas

| Serviço | Estratégia | Resultado esperado |
|---------|------------|--------------------|
| Backend | multi-stage `python:3.12-slim` + uvicorn workers | processo leve (~2 workers) |
| Frontend | Next.js `output: 'standalone'` multi-stage | runtime ~100–150MB (vs ~1GB com `node_modules`) |

Não monte código-fonte como volume em produção (já é o comportamento de `compose.prod.yaml`).

## 5. Verificação pós-deploy

```bash
curl -I https://SEU_DOMINIO/
curl -s https://SEU_DOMINIO/api/health
curl -s https://SEU_DOMINIO/robots.txt
curl -s https://SEU_DOMINIO/sitemap.xml | head
```

Login admin: `https://SEU_DOMINIO/admin/login`

## 6. Operação

```bash
# logs
docker compose -f infra/compose.prod.yaml logs -f backend

# atualizar
git pull
docker compose -f infra/compose.prod.yaml --env-file .env.prod up -d --build

# backup Postgres
docker compose -f infra/compose.prod.yaml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup-$(date +%F).sql
```

## 7. Recursos na VPS 2GB

- `WEB_CONCURRENCY=2` (backend)
- Sem `--reload` / sem bind mounts
- Postgres Alpine + Nginx Alpine
- Evite rodar Swagger/devtools em produção (`APP_ENV=production`)
