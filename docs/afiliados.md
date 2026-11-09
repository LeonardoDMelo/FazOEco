# Afiliados e transparência

## Modelo

A FazOEco **não vende produtos**. O portal compara ofertas e redireciona o usuário para marketplaces parceiros através de links de afiliado. Se a compra for concluída na loja, a FazOEco pode receber comissão.

## Fluxo da oferta

1. Conector coleta preço/disponibilidade (simulado ou live)
2. `PricingService` calcula desconto e faixa; rejeita ofertas fora dos critérios
3. `RankingService` atribui score 0–100
4. `DeduplicationService` evita duplicatas (GTIN / loja+ID)
5. Oferta entra como `pending` (ou regras do job de ingestão)
6. Admin aprova → `approval_status=approved` → aparece na vitrine pública
7. Revalidação periódica pode marcar `is_available=false` (expirada) sem apagar a página (SEO)

## Disclosure

O frontend exibe aviso de afiliados (barra + páginas institucionais):

- `/transparencia`
- `/termos`
- `/privacidade`

## Links

- Amazon Associates (`amazon_associates`)
- Mercado Livre Affiliates (`mercado_livre_affiliates`)
- Shopee Affiliates (`shopee_affiliates`)

Configure tags/IDs no `.env` / `.env.prod` antes de desligar `ENABLE_SIMULATION_MODE`.

## Boas práticas

- Nunca prometa preço final — o marketplace define o valor no checkout
- Mantenha `last_checked_at` atualizado via job de revalidação
- Prefira descontos ≥ 20% na ingestão automática (regra do scheduler)
