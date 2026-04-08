#!/usr/bin/env python3
"""Gera o PDF de implantacao do DASH_Bling."""

from fpdf import FPDF
from datetime import datetime


def sanitize(text):
    return text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2022", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'")


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "DASH_Bling - Documento de Implantacao", align="L")
            self.cell(0, 8, f"Pagina {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 14, 200, 14)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Confidencial", align="C")

    def titulo(self, texto, nivel=1):
        sizes = {1: 18, 2: 14, 3: 12}
        colors = {1: (43, 63, 29), 2: (75, 85, 50), 3: (100, 110, 70)}
        self.ln(4 if nivel > 1 else 8)
        self.set_font("Helvetica", "B", sizes.get(nivel, 12))
        self.set_text_color(*colors.get(nivel, (0, 0, 0)))
        self.multi_cell(0, 8, texto)
        if nivel == 1:
            self.set_draw_color(139, 140, 74)
            self.set_line_width(0.8)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        self.ln(2)

    def corpo(self, texto):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, sanitize(texto))
        self.ln(1)

    def item(self, texto, indent=5):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(indent)
        self.cell(5, 5.5, "-")
        self.multi_cell(170, 5.5, sanitize(texto))

    def codigo(self, texto):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        for line in texto.strip().split("\n"):
            self.cell(5)
            self.cell(0, 5, f"  {line}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def tabela(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(75, 85, 50)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(40, 40, 40)
        alt = False
        for row in rows:
            if alt:
                self.set_fill_color(248, 248, 248)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 7
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, str(cell)[:50], border=1, fill=True)
            self.ln()
            alt = not alt
        self.ln(3)

    def destaque(self, texto):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(255, 248, 220)
        self.set_text_color(100, 80, 0)
        self.cell(5)
        self.cell(180, 7, f"  {texto}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(40, 40, 40)
        self.ln(2)


def gerar():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # === CAPA ===
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(43, 63, 29)
    pdf.cell(0, 15, "DASH_Bling", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(100, 110, 70)
    pdf.cell(0, 10, "Documento de Implantacao", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(139, 140, 74)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Bling ERP x Mercado Livre - Sync Dashboard", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "NFe, SEFAZ, Produtos, Pedidos e Estoque", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Versao 1.0 | {datetime.now().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Classificacao: Confidencial", align="C", new_x="LMARGIN", new_y="NEXT")

    # === INDICE ===
    pdf.add_page()
    pdf.titulo("Indice", 1)
    indice = [
        "1. Visao Geral da Aplicacao",
        "2. Arquitetura e Stack Tecnologico",
        "3. Estrutura do Projeto",
        "4. Funcionalidades Detalhadas",
        "5. Fluxo OAuth2 (Bling)",
        "6. Geracao de NFe e Integracao SEFAZ",
        "7. Algoritmos de Sincronismo",
        "8. Seguranca",
        "9. Variaveis de Ambiente",
        "10. Guia de Instalacao",
        "11. Deploy em Servidor (cPanel / VPS)",
        "12. CI/CD - Integracao Continua",
        "13. Monitoramento e Manutencao",
        "14. Troubleshooting",
    ]
    for item in indice:
        pdf.corpo(item)

    # === 1. VISAO GERAL ===
    pdf.add_page()
    pdf.titulo("1. Visao Geral da Aplicacao", 1)
    pdf.corpo(
        "O DASH_Bling e um dashboard de sincronismo entre o Bling ERP e o Mercado Livre. "
        "A aplicacao monitora em tempo real produtos, pedidos e estoque entre as duas plataformas, "
        "identifica divergencias e permite gerenciar Notas Fiscais Eletronicas (NFe) com integracao "
        "direta ao SEFAZ."
    )
    pdf.ln(2)
    pdf.titulo("Principais Funcionalidades", 2)
    funcionalidades = [
        "Comparacao automatica de produtos por SKU (preco, nome, existencia)",
        "Comparacao de pedidos entre Bling e Mercado Livre",
        "Monitoramento de divergencias de estoque em tempo real",
        "Geracao, reenvio e cancelamento de NFe com integracao SEFAZ",
        "Exportacao de produtos para Excel com imagens",
        "Dashboard consolidado com indicador de saude do sincronismo",
        "Autenticacao OAuth2 com refresh automatico de tokens",
        "Autenticacao HTTP Basic para proteger o dashboard",
        "Rate limiting para prevencao de abuso",
    ]
    for f in funcionalidades:
        pdf.item(f)

    # === 2. ARQUITETURA ===
    pdf.add_page()
    pdf.titulo("2. Arquitetura e Stack Tecnologico", 1)
    pdf.tabela(
        ["Componente", "Tecnologia", "Versao"],
        [
            ["Backend / Framework", "FastAPI (async)", ">= 0.115"],
            ["Servidor ASGI", "Uvicorn", ">= 0.34"],
            ["HTTP Client", "HTTPX (async)", ">= 0.28"],
            ["Configuracao", "Pydantic Settings", ">= 2.9"],
            ["Templates", "Jinja2", ">= 3.1"],
            ["Exportacao Excel", "openpyxl", ">= 3.1"],
            ["Frontend", "Vanilla JS + Chart.js 4.4.7", "CDN"],
            ["Linguagem", "Python", "3.9+"],
        ],
        [65, 75, 50],
    )
    pdf.corpo(
        "A aplicacao utiliza arquitetura async com FastAPI, permitindo chamadas paralelas "
        "as APIs do Bling e Mercado Livre via asyncio.gather(). Nao utiliza banco de dados — "
        "todas as consultas sao feitas em tempo real diretamente nas APIs das plataformas."
    )

    # === 3. ESTRUTURA ===
    pdf.titulo("3. Estrutura do Projeto", 1)
    pdf.codigo(
        "app/\n"
        "  main.py               # Rotas, middleware, auth\n"
        "  config.py             # Pydantic Settings (.env)\n"
        "  clients/\n"
        "    bling.py            # Cliente Bling API v3 + NFe\n"
        "    mercadolivre.py     # Cliente Mercado Livre API\n"
        "  models/\n"
        "    schemas.py          # Product, Order, StockItem\n"
        "  services/\n"
        "    sync_products.py    # Comparacao de produtos\n"
        "    sync_orders.py      # Comparacao de pedidos\n"
        "    sync_stock.py       # Comparacao de estoque\n"
        "  templates/            # 5 paginas HTML (Jinja2)\n"
        "  static/               # Logo e assets\n"
        "requirements.txt        # Dependencias Python\n"
        "install.sh              # Script de instalacao\n"
        ".github/workflows/ci.yml  # Pipeline CI/CD"
    )

    # === 4. FUNCIONALIDADES ===
    pdf.add_page()
    pdf.titulo("4. Funcionalidades Detalhadas", 1)

    pdf.titulo("4.1 Dashboard Consolidado (/)", 2)
    pdf.corpo(
        "Pagina principal com visao unificada do sincronismo. Exibe indicador de saude (0-100%), "
        "cards de resumo (produtos, pedidos, estoque), graficos de comparacao (Chart.js) e "
        "tabelas de divergencias com filtro por severidade. Os dados sao carregados via "
        "4 chamadas paralelas a API interna."
    )

    pdf.titulo("4.2 Pagina Bling (/bling)", 2)
    pdf.corpo(
        "Visao independente dos dados do Bling. Exibe total de produtos, estoque, receita, "
        "pedidos recentes e permite exportar produtos para Excel (com imagens) filtrado por "
        "canal de venda. Inclui graficos de top 15 produtos por estoque e distribuicao de status."
    )

    pdf.titulo("4.3 Pagina Mercado Livre (/ml)", 2)
    pdf.corpo(
        "Visao independente dos anuncios e pedidos do ML. Identifica anuncios sem SKU vinculado."
    )

    pdf.titulo("4.4 Gestao de Pedidos (/bling/pedidos)", 2)
    pdf.corpo(
        "Listagem avancada com ordenacao por coluna, busca, cards de resumo (total, receita, "
        "ticket medio, clientes unicos). Cada pedido mostra status da NFe com badge colorido. "
        "Clique no badge abre modal com chave de acesso e link direto para consulta SEFAZ."
    )

    pdf.titulo("4.5 Detalhe do Pedido (/bling/pedidos/{id})", 2)
    pdf.corpo(
        "Pagina completa com informacoes do cliente, itens, frete, parcelas e contas a receber. "
        "Permite gerar NFe, reenviar NFe pendente, cancelar NFe autorizada e consultar SEFAZ."
    )

    # === 5. OAUTH2 ===
    pdf.add_page()
    pdf.titulo("5. Fluxo OAuth2 (Bling)", 1)
    pdf.corpo("O Bling utiliza OAuth2 Authorization Code Flow para autenticacao:")
    pdf.ln(2)

    pdf.titulo("Etapa 1: Inicio da Autorizacao", 3)
    pdf.corpo(
        "Usuario acessa /bling/auth. O sistema gera um state aleatorio (secrets.token_hex) "
        "e redireciona para https://www.bling.com.br/Api/v3/oauth/authorize com client_id, "
        "redirect_uri e response_type=code."
    )

    pdf.titulo("Etapa 2: Autorizacao no Bling", 3)
    pdf.corpo(
        "Usuario faz login no Bling e autoriza o aplicativo. Bling redireciona de volta para "
        "o callback com um authorization code."
    )

    pdf.titulo("Etapa 3: Troca de Codigo por Tokens", 3)
    pdf.corpo(
        "O callback (/bling/callback) recebe o code e faz POST para o token endpoint "
        "com Basic Auth (base64 de client_id:client_secret). Recebe access_token e refresh_token."
    )

    pdf.titulo("Etapa 4: Persistencia de Tokens", 3)
    pdf.corpo(
        "Tokens sao salvos em bling_tokens.json codificados em Base64 com permissao chmod 600 "
        "(somente leitura/escrita pelo dono)."
    )

    pdf.titulo("Etapa 5: Refresh Automatico", 3)
    pdf.corpo(
        "Quando o access_token expira (resposta 401), o sistema automaticamente usa o "
        "refresh_token para obter novos tokens. Se o refresh_token tambem expirar, "
        "o usuario precisa re-autorizar via /bling/auth."
    )

    # === 6. NFe ===
    pdf.add_page()
    pdf.titulo("6. Geracao de NFe e Integracao SEFAZ", 1)
    pdf.corpo(
        "O sistema gerencia todo o ciclo de vida da Nota Fiscal Eletronica, "
        "desde a geracao ate o cancelamento, com integracao direta ao SEFAZ."
    )
    pdf.ln(2)

    pdf.titulo("6.1 Processo de Geracao", 2)
    steps = [
        "1. Verificar se ja existe NFe vinculada ao pedido (por ID ou por contato+valor)",
        "2. Buscar dados completos: pedido, itens, contato, endereco de entrega (etiqueta)",
        "3. Montar payload da NFe (tipo, contato com CPF/CNPJ, itens, parcelas, transporte)",
        "4. POST para /nfe na API do Bling (cria a nota com status Pendente)",
        "5. POST para /nfe/{id}/enviar (submete ao SEFAZ automaticamente)",
        "6. Verificar resposta XML do SEFAZ (cStat=100 = Autorizada)",
    ]
    for s in steps:
        pdf.item(s)
    pdf.ln(3)

    pdf.titulo("6.2 Status da NFe", 2)
    pdf.tabela(
        ["Codigo", "Status", "Acao"],
        [
            ["1", "Pendente", "Aguardando envio ao SEFAZ"],
            ["2", "Rejeitada", "Corrigir dados e reenviar"],
            ["3", "Denegada", "Verificar com fiscal"],
            ["4", "Cancelada", "Gerar nova se necessario"],
            ["5", "Autorizada", "Sucesso - PDF/XML disponiveis"],
            ["6", "Inutilizada", "NFe anulada"],
        ],
        [25, 50, 115],
    )

    pdf.titulo("6.3 Reenvio e Cancelamento", 2)
    pdf.corpo(
        "NFe pendente (status 1): O botao 'Corrigir e Reenviar' reconstroi o payload "
        "com dados atualizados do pedido, faz PUT na NFe existente e reenvia ao SEFAZ. "
        "NFe autorizada (status 5): O botao 'Cancelar' envia POST para /nfe/{id}/cancelar."
    )

    # === 7. ALGORITMOS ===
    pdf.add_page()
    pdf.titulo("7. Algoritmos de Sincronismo", 1)

    pdf.titulo("7.1 Comparacao de Produtos", 2)
    pdf.corpo(
        "Indexa produtos de ambas plataformas por SKU. Para cada SKU presente em ambas, "
        "compara preco (tolerancia de R$0.01) e nome (case-insensitive). SKUs presentes "
        "em apenas uma plataforma sao marcados como 'missing' com severidade 'error'."
    )

    pdf.titulo("7.2 Comparacao de Pedidos", 2)
    pdf.corpo(
        "Indexa pedidos por order_id. Compara total e status entre plataformas. "
        "Status do ML sao normalizados: paid->em aberto, shipped/delivered->atendido, "
        "cancelled->cancelado. Divergencias de status e valor sao classificadas como 'warning'."
    )

    pdf.titulo("7.3 Comparacao de Estoque", 2)
    pdf.corpo(
        "Para cada SKU, calcula diferenca = estoque_bling - estoque_ml. "
        "Divergencias sao ordenadas por |diferenca| decrescente. Identifica itens "
        "com estoque zero em apenas uma plataforma. O indicador de saude geral e "
        "calculado como: (total_synced / total_items) * 100."
    )

    # === 8. SEGURANCA ===
    pdf.add_page()
    pdf.titulo("8. Seguranca", 1)

    pdf.titulo("8.1 Autenticacao do Dashboard", 2)
    pdf.corpo(
        "Todos os endpoints sao protegidos com HTTP Basic Auth. A verificacao usa "
        "secrets.compare_digest() para prevenir timing attacks. Credenciais definidas "
        "via variaveis de ambiente DASH_USERNAME e DASH_PASSWORD."
    )

    pdf.titulo("8.2 Rate Limiting", 2)
    pdf.corpo(
        "Middleware customizado limita a 30 requisicoes por minuto por IP. "
        "Retorna HTTP 429 quando excedido. Alem disso, os clientes de API "
        "respeitam limites das plataformas: Bling ~3 req/s, ML ~5 req/s."
    )

    pdf.titulo("8.3 Protecao de Dados", 2)
    medidas = [
        "Credenciais em .env (fora do git, permissao 600)",
        "Tokens OAuth em base64 com chmod 600",
        "Endpoints /docs e /redoc desabilitados em producao",
        "Mensagens de erro sanitizadas (sem detalhes internos)",
        "XSS mitigado: error containers usam textContent",
        "Validacao de entrada: datas validadas via regex YYYY-MM-DD",
        ".htaccess bloqueia acesso a .py, .env, .log, app/, venv/",
    ]
    for m in medidas:
        pdf.item(m)

    # === 9. VARIAVEIS ===
    pdf.add_page()
    pdf.titulo("9. Variaveis de Ambiente", 1)
    pdf.tabela(
        ["Variavel", "Descricao", "Obrigatoria"],
        [
            ["BLING_CLIENT_ID", "Client ID do app OAuth (Bling)", "Sim"],
            ["BLING_CLIENT_SECRET", "Client Secret do app OAuth", "Sim"],
            ["BLING_ACCESS_TOKEN", "Token de acesso (preenchido via OAuth)", "Nao"],
            ["BLING_REFRESH_TOKEN", "Token de refresh (preenchido via OAuth)", "Nao"],
            ["BLING_REDIRECT_URI", "URL de callback OAuth", "Sim"],
            ["ML_CLIENT_ID", "Client ID Mercado Livre", "Sim*"],
            ["ML_CLIENT_SECRET", "Client Secret Mercado Livre", "Sim*"],
            ["ML_ACCESS_TOKEN", "Token de acesso ML", "Sim*"],
            ["ML_SELLER_ID", "ID do vendedor ML", "Sim*"],
            ["DASH_USERNAME", "Usuario do dashboard", "Sim"],
            ["DASH_PASSWORD", "Senha do dashboard", "Sim"],
            ["BASE_PATH", "Prefixo de URL (ex: /dash)", "Nao"],
        ],
        [55, 100, 35],
    )
    pdf.corpo("* Obrigatorio apenas se o modulo Mercado Livre for utilizado.")

    # === 10. INSTALACAO ===
    pdf.add_page()
    pdf.titulo("10. Guia de Instalacao", 1)

    pdf.titulo("10.1 Requisitos", 2)
    pdf.item("Python 3.9 ou superior")
    pdf.item("pip (gerenciador de pacotes Python)")
    pdf.item("Acesso a internet (APIs Bling e ML)")
    pdf.item("Credenciais OAuth do Bling (painel de desenvolvedor)")
    pdf.ln(3)

    pdf.titulo("10.2 Instalacao Automatica", 2)
    pdf.corpo("O projeto inclui um script de instalacao automatica:")
    pdf.codigo(
        "git clone https://github.com/coliveira1977/DASH_Bling.git\n"
        "cd DASH_Bling\n"
        "chmod +x install.sh\n"
        "./install.sh"
    )
    pdf.corpo(
        "O script verifica Python, cria virtualenv, instala dependencias, "
        "configura permissoes e valida que a aplicacao carrega corretamente."
    )

    pdf.titulo("10.3 Instalacao Manual", 2)
    pdf.codigo(
        "python3 -m venv venv\n"
        "source venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "cp .env.example .env\n"
        "nano .env  # editar credenciais\n"
        "uvicorn app.main:app --reload --port 8000"
    )

    pdf.titulo("10.4 Primeiro Acesso", 2)
    pdf.item("Acesse http://localhost:8000 (login com DASH_USERNAME/DASH_PASSWORD)")
    pdf.item("Va em Bling > Autorizar para completar o fluxo OAuth2")
    pdf.item("Apos autorizar, os dados do Bling aparecerao automaticamente")

    # === 11. DEPLOY ===
    pdf.add_page()
    pdf.titulo("11. Deploy em Servidor", 1)

    pdf.titulo("11.1 Deploy VPS (Recomendado)", 2)
    pdf.corpo("Para servidores Ubuntu/Debian com acesso root:")
    pdf.codigo(
        "# 1. Copiar projeto\n"
        "scp -r . user@servidor:/var/www/dash-bling/\n\n"
        "# 2. Instalar\n"
        "ssh user@servidor\n"
        "cd /var/www/dash-bling\n"
        "./install.sh\n\n"
        "# 3. Criar servico systemd\n"
        "sudo nano /etc/systemd/system/dash-bling.service"
    )
    pdf.corpo("Conteudo do servico systemd:")
    pdf.codigo(
        "[Unit]\n"
        "Description=DASH_Bling Sync Dashboard\n"
        "After=network.target\n\n"
        "[Service]\n"
        "User=www-data\n"
        "WorkingDirectory=/var/www/dash-bling\n"
        'Environment="PATH=/var/www/dash-bling/venv/bin"\n'
        "ExecStart=/var/www/dash-bling/venv/bin/uvicorn "
        "app.main:app --host 0.0.0.0 --port 8000\n"
        "Restart=always\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target"
    )
    pdf.codigo(
        "sudo systemctl enable dash-bling\n"
        "sudo systemctl start dash-bling"
    )

    pdf.titulo("11.2 Nginx Reverse Proxy", 2)
    pdf.codigo(
        "server {\n"
        "    listen 80;\n"
        "    server_name dash.exemplo.com;\n\n"
        "    location / {\n"
        "        proxy_pass http://127.0.0.1:8000;\n"
        "        proxy_set_header Host $host;\n"
        "        proxy_set_header X-Real-IP $remote_addr;\n"
        "        proxy_set_header X-Forwarded-Proto $scheme;\n"
        "    }\n"
        "}\n\n"
        "# SSL com Let's Encrypt:\n"
        "sudo certbot --nginx -d dash.exemplo.com"
    )

    pdf.titulo("11.3 Deploy cPanel (Hospedagem Compartilhada)", 2)
    pdf.corpo(
        "Para hospedagem compartilhada sem acesso root, a aplicacao usa um gateway CGI "
        "(dispatch.cgi) que roda o FastAPI via Starlette TestClient. O .htaccess faz "
        "rewrite de todas as requisicoes para o CGI. Requer BASE_PATH definido."
    )
    pdf.codigo(
        "# Estrutura no servidor:\n"
        "~/public_html/dash/\n"
        "  dispatch.cgi    # Gateway CGI (chmod 700)\n"
        "  .htaccess       # Rewrite + protecao de arquivos\n"
        "  app/            # Codigo da aplicacao\n"
        "  venv/           # Ambiente virtual\n"
        "~/.env_dash       # Credenciais (fora do public_html)"
    )

    # === 12. CI/CD ===
    pdf.add_page()
    pdf.titulo("12. CI/CD - Integracao Continua", 1)
    pdf.corpo(
        "O projeto inclui pipeline GitHub Actions (.github/workflows/ci.yml) "
        "com tres etapas executadas a cada push ou pull request na branch main:"
    )
    pdf.ln(2)

    pdf.titulo("12.1 Lint e Teste (lint-and-test)", 2)
    pdf.corpo(
        "Executa em matriz com Python 3.9, 3.10, 3.11 e 3.12. "
        "Instala dependencias, roda linting com ruff e verifica que a aplicacao "
        "carrega sem erros."
    )

    pdf.titulo("12.2 Verificacao de Seguranca (security-check)", 2)
    pdf.corpo(
        "Audita dependencias com pip-audit para vulnerabilidades conhecidas. "
        "Busca credenciais hardcoded no codigo-fonte (.py e .html). "
        "Falha o pipeline se encontrar secrets ou dependencias vulneraveis."
    )

    pdf.titulo("12.3 Deploy Automatico (deploy)", 2)
    pdf.corpo(
        "Executado apenas em push na main (apos lint e security passarem). "
        "Conecta via SSH ao servidor, faz git pull, atualiza dependencias. "
        "Requer secrets configurados no GitHub:"
    )
    pdf.tabela(
        ["Secret", "Descricao"],
        [
            ["SERVER_HOST", "Hostname ou IP do servidor"],
            ["SERVER_USER", "Usuario SSH"],
            ["SERVER_SSH_KEY", "Chave privada SSH"],
        ],
        [60, 130],
    )

    pdf.titulo("12.4 Fluxo de Trabalho", 2)
    pdf.codigo(
        "Developer -> git push main\n"
        "  |-> GitHub Actions: lint (Python 3.9-3.12)\n"
        "  |-> GitHub Actions: security audit\n"
        "  |-> (ambos OK) -> Deploy automatico via SSH\n"
        "  |-> Servidor: git pull + pip install"
    )

    # === 13. MONITORAMENTO ===
    pdf.add_page()
    pdf.titulo("13. Monitoramento e Manutencao", 1)

    pdf.titulo("13.1 Logs", 2)
    pdf.corpo("Para VPS com systemd:")
    pdf.codigo("journalctl -u dash-bling -f  # logs em tempo real")
    pdf.corpo("Para cPanel:")
    pdf.codigo("cat ~/public_html/dash/uvicorn.log")

    pdf.titulo("13.2 Tokens OAuth", 2)
    pdf.corpo(
        "O access_token do Bling expira periodicamente. O sistema tenta refresh automatico. "
        "Se o refresh_token tambem expirar, o dashboard mostrara erro 401 e o usuario "
        "precisa re-autorizar via /bling/auth."
    )

    pdf.titulo("13.3 Rate Limits das APIs", 2)
    pdf.tabela(
        ["Plataforma", "Limite", "Delay Implementado"],
        [
            ["Bling API v3", "3 req/s", "0.34s entre requests"],
            ["Mercado Livre API", "5 req/s", "0.20s entre requests"],
            ["Dashboard (global)", "30 req/min por IP", "Middleware FastAPI"],
        ],
        [60, 60, 70],
    )

    pdf.titulo("13.4 Backup", 2)
    pdf.item("Arquivo .env: contem credenciais (backup seguro obrigatorio)")
    pdf.item("bling_tokens.json: tokens OAuth (recriavel via re-autorizacao)")
    pdf.item("Codigo: versionado no GitHub (DASH_Bling)")

    # === 14. TROUBLESHOOTING ===
    pdf.add_page()
    pdf.titulo("14. Troubleshooting", 1)

    problemas = [
        (
            "Bling nao autorizado (401)",
            "Acesse /bling/auth para completar o fluxo OAuth2. Verifique BLING_CLIENT_ID "
            "e BLING_CLIENT_SECRET no .env.",
        ),
        (
            "Token expirado",
            "O refresh automatico falhou. Delete bling_tokens.json e re-autorize via /bling/auth.",
        ),
        (
            "NFe permanece Pendente",
            "SEFAZ pode estar processando. Use o botao 'Corrigir e Reenviar'. "
            "Verifique dados do contato (CPF/CNPJ, endereco completo).",
        ),
        (
            "Erro 429 - Too Many Requests",
            "Aguarde 60 segundos. O rate limiting global e de 30 req/min por IP.",
        ),
        (
            "Produtos sem SKU no ML",
            "Anuncios do ML sem atributo SELLER_SKU nao sao vinculados. "
            "Configure o SKU na edicao do anuncio no Mercado Livre.",
        ),
        (
            "redirect_uri_mismatch (Bling OAuth)",
            "A URL de callback configurada no app Bling nao bate com BLING_REDIRECT_URI no .env. "
            "Atualize no painel de desenvolvedor do Bling.",
        ),
        (
            "Erro 500 no cPanel",
            "Verifique permissoes do dispatch.cgi (chmod 700). Teste localmente: "
            "PATH_INFO=/ REQUEST_METHOD=GET ./dispatch.cgi",
        ),
    ]

    for titulo_p, solucao in problemas:
        pdf.titulo(titulo_p, 3)
        pdf.corpo(solucao)
        pdf.ln(1)

    # === ENDPOINTS ===
    pdf.add_page()
    pdf.titulo("Anexo: Referencia de Endpoints", 1)
    pdf.tabela(
        ["Metodo", "Rota", "Descricao"],
        [
            ["GET", "/", "Dashboard consolidado"],
            ["GET", "/bling", "Pagina Bling"],
            ["GET", "/ml", "Pagina Mercado Livre"],
            ["GET", "/bling/pedidos", "Listagem de pedidos"],
            ["GET", "/bling/pedidos/{id}", "Detalhe do pedido"],
            ["GET", "/bling/auth", "Iniciar OAuth2 Bling"],
            ["GET", "/bling/callback", "Callback OAuth2"],
            ["GET", "/api/bling/summary", "Resumo Bling"],
            ["GET", "/api/bling/orders", "Lista pedidos + NFe"],
            ["GET", "/api/bling/orders/{id}", "Detalhe pedido"],
            ["GET", "/api/bling/orders/{id}/nfe", "Buscar NFe do pedido"],
            ["POST", "/api/bling/orders/{id}/nfe", "Gerar NFe + SEFAZ"],
            ["POST", "/api/bling/nfe/{id}/retry", "Reenviar NFe"],
            ["POST", "/api/bling/nfe/{id}/cancel", "Cancelar NFe"],
            ["GET", "/api/bling/nfe/{id}", "Detalhe NFe"],
            ["GET", "/api/bling/empresa", "Dados da empresa"],
            ["GET", "/api/bling/canais-venda", "Canais de venda"],
            ["GET", "/api/bling/produtos/export", "Exportar Excel"],
            ["GET", "/api/ml/summary", "Resumo ML"],
            ["GET", "/api/sync/products", "Sync produtos"],
            ["GET", "/api/sync/orders", "Sync pedidos"],
            ["GET", "/api/sync/stock", "Sync estoque"],
            ["GET", "/api/sync/summary", "Saude geral (%)"],
        ],
        [20, 75, 95],
    )

    # Salvar
    output = "/Users/chris/bling-ml-sync/DASH_Bling_Implantacao.pdf"
    pdf.output(output)
    print(f"PDF gerado: {output}")


if __name__ == "__main__":
    gerar()
