# Bling x Mercado Livre — Sync Dashboard

Dashboard de sincronismo entre **Bling ERP** e **Mercado Livre**, com gerenciamento de NFe e integração SEFAZ.

## Funcionalidades

- **Sincronismo de Produtos** — Compara produtos por SKU entre Bling e ML (preco, nome, estoque)
- **Sincronismo de Pedidos** — Detecta pedidos divergentes ou ausentes entre plataformas
- **Sincronismo de Estoque** — Monitora diferencas de estoque em tempo real
- **Gerenciamento de NFe** — Gerar, reenviar, cancelar notas fiscais com integracao SEFAZ
- **Exportacao Excel** — Exporta produtos com imagens, filtrado por canal de venda
- **Dashboard Consolidado** — Indicador de saude do sincronismo com graficos e divergencias
- **OAuth2 Bling** — Autenticacao segura com refresh automatico de tokens

## Stack

| Componente | Tecnologia |
|------------|-----------|
| Backend | FastAPI (async) |
| Servidor | Uvicorn |
| HTTP Client | HTTPX (async) |
| Templates | Jinja2 |
| Validacao | Pydantic v2 |
| Exportacao | openpyxl |
| Frontend | Vanilla JS + Chart.js |

## Estrutura

```
app/
├── main.py                  # Rotas e endpoints FastAPI
├── config.py                # Configuracoes (Pydantic Settings)
├── clients/
│   ├── bling.py             # Cliente Bling API v3 (OAuth2, NFe, SEFAZ)
│   └── mercadolivre.py      # Cliente Mercado Livre API
├── models/
│   └── schemas.py           # Modelos Pydantic (Product, Order, StockItem)
├── services/
│   ├── sync_products.py     # Comparacao de produtos por SKU
│   ├── sync_orders.py       # Comparacao de pedidos por ID
│   └── sync_stock.py        # Comparacao de niveis de estoque
├── templates/
│   ├── dashboard.html       # Painel consolidado de sincronismo
│   ├── bling.html           # Visao independente Bling
│   ├── ml.html              # Visao independente Mercado Livre
│   ├── bling_orders.html    # Listagem de pedidos Bling
│   └── bling_order_detail.html  # Detalhe do pedido + NFe
└── static/
    └── logo.png
```

## Endpoints

### Paginas

| Rota | Descricao |
|------|-----------|
| `GET /` | Dashboard consolidado |
| `GET /bling` | Pagina Bling (produtos, pedidos, exportacao) |
| `GET /ml` | Pagina Mercado Livre |
| `GET /bling/pedidos` | Listagem de pedidos |
| `GET /bling/pedidos/{id}` | Detalhe do pedido + NFe |

### API Bling

| Rota | Descricao |
|------|-----------|
| `GET /api/bling/summary` | Resumo de produtos e pedidos |
| `GET /api/bling/orders` | Lista pedidos com status NFe |
| `GET /api/bling/orders/{id}` | Detalhe completo do pedido |
| `GET /api/bling/orders/{id}/contas-receber` | Contas a receber do pedido |
| `GET /api/bling/canais-venda` | Canais de venda cadastrados |
| `GET /api/bling/empresa` | Dados da empresa (CNPJ, endereco) |
| `GET /api/bling/produtos/export` | Exportar produtos em Excel |

### API NFe

| Rota | Descricao |
|------|-----------|
| `GET /api/bling/orders/{id}/nfe` | Buscar NFe existente do pedido |
| `POST /api/bling/orders/{id}/nfe` | Gerar NFe e enviar ao SEFAZ |
| `POST /api/bling/nfe/{id}/retry` | Corrigir e reenviar NFe pendente |
| `POST /api/bling/nfe/{id}/cancel` | Cancelar NFe autorizada |
| `GET /api/bling/nfe/{id}` | Detalhe da NFe |

### API Mercado Livre

| Rota | Descricao |
|------|-----------|
| `GET /api/ml/summary` | Resumo de anuncios e pedidos |

### API Sincronismo

| Rota | Descricao |
|------|-----------|
| `GET /api/sync/products` | Comparar produtos Bling x ML |
| `GET /api/sync/orders` | Comparar pedidos Bling x ML |
| `GET /api/sync/stock` | Comparar estoque Bling x ML |
| `GET /api/sync/summary` | Resumo geral + % saude do sincronismo |

## Configuracao

### 1. Variaveis de ambiente (.env)

```env
# Bling API v3 (OAuth2)
BLING_CLIENT_ID=seu_client_id
BLING_CLIENT_SECRET=seu_client_secret
BLING_ACCESS_TOKEN=
BLING_REFRESH_TOKEN=
BLING_REDIRECT_URI=http://localhost:8000/bling/callback

# Mercado Livre API
ML_CLIENT_ID=seu_client_id_ml
ML_CLIENT_SECRET=seu_client_secret_ml
ML_ACCESS_TOKEN=seu_access_token_ml
ML_REFRESH_TOKEN=seu_refresh_token_ml
ML_SELLER_ID=seu_seller_id_ml
```

### 2. Instalacao

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Execucao local

```bash
uvicorn app.main:app --reload --port 8000
```

Acesse http://localhost:8000

### 4. Autorizar Bling

Acesse `/bling/auth` para iniciar o fluxo OAuth2. Apos autorizar, os tokens sao salvos em `bling_tokens.json`.

## Deploy (Hospedagem Compartilhada / cPanel)

O projeto pode rodar em hospedagem compartilhada via CGI:

1. Copiar arquivos para `~/public_html/dash/`
2. Criar virtualenv e instalar dependencias
3. Configurar `dispatch.cgi` como gateway CGI para FastAPI
4. Configurar `.htaccess` com rewrite para o CGI
5. Mover `.env` para fora do `public_html` por seguranca
6. Definir `BASE_PATH=/dash` para corrigir rotas sob subdiretorio

### Protecao de arquivos

O `.htaccess` bloqueia acesso HTTP a:
- Arquivos `.py`, `.env`, `.log`, `.json`
- Diretorios `app/`, `venv/`, `__pycache__/`

## Rate Limiting

| Plataforma | Limite |
|------------|--------|
| Bling API | ~3 req/s (0.34s delay) |
| Mercado Livre API | ~5 req/s (0.2s delay) |
