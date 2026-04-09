import httpx
import asyncio
import json
import stat
import secrets
from base64 import b64encode, b64decode
from pathlib import Path
from app.config import get_settings
from app.models.schemas import Product, Order

BASE_URL = "https://www.bling.com.br/Api/v3"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
RATE_LIMIT_DELAY = 0.34  # ~3 requests/second
TOKEN_FILE = Path("bling_tokens.json")


class BlingClient:
    def __init__(self):
        settings = get_settings()
        self.client_id = settings.bling_client_id
        self.client_secret = settings.bling_client_secret
        self.access_token = settings.bling_access_token
        self.refresh_token = settings.bling_refresh_token
        self.redirect_uri = settings.bling_redirect_uri
        self._client: httpx.AsyncClient | None = None
        self._load_saved_tokens()

    def _load_saved_tokens(self):
        """Load tokens from file if they exist (overrides .env)."""
        if TOKEN_FILE.exists():
            try:
                raw = TOKEN_FILE.read_text()
                data = json.loads(b64decode(raw).decode())
                self.access_token = data.get("access_token", self.access_token)
                self.refresh_token = data.get("refresh_token", self.refresh_token)
            except Exception:
                pass

    def _save_tokens(self):
        """Persist tokens to file with obfuscation and restricted permissions."""
        payload = b64encode(json.dumps({
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }).encode()).decode()
        TOKEN_FILE.write_text(payload)
        TOKEN_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _basic_auth(self) -> str:
        credentials = b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        return f"Basic {credentials}"

    def get_authorize_url(self) -> str:
        state = secrets.token_hex(16)
        return (
            f"https://www.bling.com.br/Api/v3/oauth/authorize"
            f"?response_type=code&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&state={state}"
        )

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                headers={
                    "Authorization": self._basic_auth(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self._save_tokens()
            self._client = None
            return data

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        client = await self._get_client()
        await asyncio.sleep(RATE_LIMIT_DELAY)
        response = await client.request(method, endpoint, **kwargs)

        if response.status_code == 401:
            await self._refresh_access_token()
            client = await self._get_client()
            response = await client.request(method, endpoint, **kwargs)

        response.raise_for_status()
        return response.json()

    async def _refresh_access_token(self):
        """Use refresh_token to get a new access_token."""
        if not self.refresh_token:
            raise RuntimeError(
                "Token expirado. Acesse /bling/auth para reconectar."
            )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TOKEN_URL,
                headers={
                    "Authorization": self._basic_auth(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
            )
            if response.status_code >= 400:
                # Refresh token expired, need to re-authorize
                TOKEN_FILE.unlink(missing_ok=True)
                self.access_token = ""
                self.refresh_token = ""
                raise RuntimeError(
                    "Token expirado. Acesse /bling/auth para reconectar."
                )
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self._save_tokens()
            self._client = None

    async def get_products_raw(self) -> list[dict]:
        """Fetch all products with full detail for export."""
        products = []
        page = 1
        while True:
            data = await self._request(
                "GET", "/produtos", params={"pagina": page, "limite": 100}
            )
            items = data.get("data", [])
            if not items:
                break
            products.extend(items)
            if len(items) < 100:
                break
            page += 1
        return products

    async def get_products(self) -> list[Product]:
        products = []
        page = 1

        while True:
            data = await self._request(
                "GET", "/produtos", params={"pagina": page, "limite": 100}
            )

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                stock = 0
                if item.get("estoque", {}).get("saldoVirtualTotal") is not None:
                    stock = int(item["estoque"]["saldoVirtualTotal"])

                products.append(
                    Product(
                        sku=item.get("codigo", ""),
                        name=item.get("nome", ""),
                        price=float(item.get("preco", 0)),
                        stock=stock,
                        source="bling",
                        external_id=str(item.get("id", "")),
                    )
                )

            if len(items) < 100:
                break
            page += 1

        return products

    async def get_orders(
        self, date_from: str, date_to: str
    ) -> list[Order]:
        orders = []
        page = 1

        while True:
            data = await self._request(
                "GET",
                "/pedidos/vendas",
                params={
                    "pagina": page,
                    "limite": 100,
                    "dataInicial": date_from,
                    "dataFinal": date_to,
                },
            )

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                orders.append(
                    Order(
                        order_id=str(item.get("numero", "")),
                        date=item.get("data", ""),
                        total=float(item.get("total", 0)),
                        status=str(item.get("situacao", {}).get("valor", "")),
                        items_count=len(item.get("itens", [])),
                        source="bling",
                        buyer=item.get("contato", {}).get("nome", ""),
                    )
                )

            if len(items) < 100:
                break
            page += 1

        return orders

    async def get_orders_raw(
        self, date_from: str, date_to: str
    ) -> list[dict]:
        """Returns raw order data from the API (for listing page)."""
        orders = []
        page = 1
        while True:
            data = await self._request(
                "GET",
                "/pedidos/vendas",
                params={
                    "pagina": page,
                    "limite": 100,
                    "dataInicial": date_from,
                    "dataFinal": date_to,
                },
            )
            items = data.get("data", [])
            if not items:
                break
            orders.extend(items)
            if len(items) < 100:
                break
            page += 1
        return orders

    async def get_orders_location_count(
        self, date_from: str, date_to: str
    ) -> dict:
        """Count orders by UF and city using contact addresses."""
        orders = await self.get_orders_raw(date_from, date_to)
        contato_ids = set()
        order_contatos = []
        for o in orders:
            cid = o.get("contato", {}).get("id", 0)
            if cid:
                contato_ids.add(cid)
                order_contatos.append(cid)

        # Fetch contacts in parallel (batches of 10)
        contato_locations: dict[int, dict] = {}
        id_list = list(contato_ids)
        for i in range(0, len(id_list), 10):
            batch = id_list[i:i+10]
            results = await asyncio.gather(
                *[self._safe_get_contato_location(cid) for cid in batch]
            )
            for cid, loc in zip(batch, results):
                if loc.get("uf"):
                    contato_locations[cid] = loc

        uf_count: dict[str, int] = {}
        city_count: dict[str, int] = {}
        for cid in order_contatos:
            loc = contato_locations.get(cid)
            if not loc:
                continue
            uf = loc["uf"]
            cidade = loc.get("municipio", "")
            uf_count[uf] = uf_count.get(uf, 0) + 1
            if cidade:
                key = f"{cidade}/{uf}"
                city_count[key] = city_count.get(key, 0) + 1

        return {"by_uf": uf_count, "by_city": city_count}

    async def _safe_get_contato_location(self, contato_id: int) -> dict:
        """Get UF and city from a contact."""
        try:
            data = await self._request("GET", f"/contatos/{contato_id}")
            contato = data.get("data", {})
            endereco = contato.get("endereco", {}).get("geral", {})
            return {
                "uf": (endereco.get("uf", "") or "").upper().strip(),
                "municipio": (endereco.get("municipio", "") or "").strip(),
            }
        except Exception:
            return {}

    async def get_order_detail(self, order_id: int) -> dict:
        """Fetch full order detail by Bling internal ID."""
        data = await self._request("GET", f"/pedidos/vendas/{order_id}")
        return data.get("data", {})

    async def get_nfe_list(self) -> list[dict]:
        """Fetch all NFes to build a lookup of contato -> nfe status."""
        nfes = []
        page = 1
        while True:
            data = await self._request(
                "GET", "/nfe", params={"pagina": page, "limite": 100}
            )
            items = data.get("data", [])
            if not items:
                break
            nfes.extend(items)
            if len(items) < 100:
                break
            page += 1
        return nfes

    async def get_nfe(self, nfe_id: int) -> dict:
        """Fetch NFe detail including linkPDF and linkDanfe."""
        data = await self._request("GET", f"/nfe/{nfe_id}")
        return data.get("data", {})

    async def get_empresa(self) -> dict:
        """Extract company data from the emitente of an existing NFe XML."""
        from xml.etree import ElementTree as ET

        nfes = await self._request("GET", "/nfe", params={"pagina": 1, "limite": 5})
        for nfe_item in nfes.get("data", []):
            nfe_detail = await self._request("GET", f"/nfe/{nfe_item['id']}")
            xml_url = nfe_detail.get("data", {}).get("xml", "")
            if not xml_url:
                continue
            client = await self._get_client()
            resp = await client.get(xml_url)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.text)
            ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
            emit = root.find(".//nfe:emit", ns)
            if emit is None:
                continue
            def txt(parent, tag):
                el = parent.find(f"nfe:{tag}", ns)
                return el.text if el is not None else ""
            end_emit = emit.find("nfe:enderEmit", ns)
            return {
                "cnpj": txt(emit, "CNPJ"),
                "razaoSocial": txt(emit, "xNome"),
                "nomeFantasia": txt(emit, "xFant"),
                "ie": txt(emit, "IE"),
                "crt": txt(emit, "CRT"),
                "endereco": {
                    "endereco": txt(end_emit, "xLgr") if end_emit is not None else "",
                    "numero": txt(end_emit, "nro") if end_emit is not None else "",
                    "bairro": txt(end_emit, "xBairro") if end_emit is not None else "",
                    "municipio": txt(end_emit, "xMun") if end_emit is not None else "",
                    "uf": txt(end_emit, "UF") if end_emit is not None else "",
                    "cep": txt(end_emit, "CEP") if end_emit is not None else "",
                },
            }
        return {}

    async def get_contas_receber_by_origin(self, origin_id: int) -> list[dict]:
        """Fetch accounts receivable linked to a sales order origin."""
        contas = []
        page = 1
        while True:
            data = await self._request(
                "GET", "/contas/receber",
                params={"pagina": page, "limite": 100},
            )
            items = data.get("data", [])
            if not items:
                break
            contas.extend(items)
            if len(items) < 100:
                break
            page += 1
        # Filter by origin ID (Bling API doesn't support server-side filtering)
        return [c for c in contas if c.get("origem", {}).get("id") == origin_id]

    async def cancel_nfe(self, nfe_id: int) -> dict:
        """Cancel an authorized NFe via Bling API."""
        data = await self._request("POST", f"/nfe/{nfe_id}/cancelar")
        return data.get("data", data)

    async def get_contato(self, contato_id: int) -> dict:
        """Fetch full contact details."""
        data = await self._request("GET", f"/contatos/{contato_id}")
        return data.get("data", {})

    async def generate_nfe(self, order_id: int) -> dict:
        """Generate NFe from a sales order.

        Gets the order detail + full contact data, then posts to /nfe.
        """
        order = await self.get_order_detail(order_id)
        if not order:
            raise ValueError("Pedido nao encontrado")

        # Check if NFe already linked in order
        nfe_id = order.get("notaFiscal", {}).get("id", 0)
        if nfe_id and nfe_id != 0:
            return await self.get_nfe(nfe_id)

        contato_pedido = order.get("contato", {})
        contato_id = contato_pedido.get("id", 0)
        order_total = order.get("total", 0)

        # Check if an NFe already exists for this contact+value
        # (Bling sometimes doesn't link notaFiscal.id back to the order)
        existing_nfes = await self.get_nfe_list()
        for nfe in existing_nfes:
            nfe_contato_id = nfe.get("contato", {}).get("id", 0)
            nfe_sit = nfe.get("situacao", 0)
            if nfe_contato_id == contato_id and nfe_sit in (1, 5):
                # Found active NFe for same contact - get detail to confirm
                nfe_detail = await self.get_nfe(nfe["id"])
                nfe_valor = nfe_detail.get("valorNota", 0)
                # Match by value to avoid cross-matching different orders
                if abs(nfe_valor - order_total) < 0.01:
                    nfe_detail["_existing"] = True
                    return nfe_detail

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        itens = order.get("itens", [])
        parcelas = order.get("parcelas", [])
        transporte = order.get("transporte", {})
        etiqueta = transporte.get("etiqueta", {})

        # Fetch full contact data for complete address
        contato_full = {}
        if contato_id:
            try:
                contato_full = await self.get_contato(contato_id)
            except Exception:
                pass

        # Build contact with full data
        end_geral = contato_full.get("endereco", {}).get("geral", {})
        # Prefer etiqueta address (shipping) over contact address
        nfe_contato = {
            "id": contato_id,
            "nome": contato_full.get("nome") or contato_pedido.get("nome", ""),
            "numeroDocumento": (
                contato_full.get("numeroDocumento")
                or contato_pedido.get("numeroDocumento", "")
            ).replace(".", "").replace("-", "").replace("/", ""),
            "ie": contato_full.get("ie", ""),
            "indicadorIe": contato_full.get("indicadorIe", 9),
            "tipo": contato_full.get("tipo") or contato_pedido.get("tipoPessoa", "F"),
            "endereco": {
                "endereco": etiqueta.get("endereco") or end_geral.get("endereco", ""),
                "numero": etiqueta.get("numero") or end_geral.get("numero", ""),
                "complemento": etiqueta.get("complemento") or end_geral.get("complemento", ""),
                "bairro": etiqueta.get("bairro") or end_geral.get("bairro", ""),
                "cep": etiqueta.get("cep") or end_geral.get("cep", ""),
                "municipio": etiqueta.get("municipio") or end_geral.get("municipio", ""),
                "uf": etiqueta.get("uf") or end_geral.get("uf", ""),
            },
        }
        if contato_full.get("email"):
            nfe_contato["email"] = contato_full["email"]

        nfe_items = []
        for item in itens:
            nfe_items.append({
                "codigo": item.get("codigo", ""),
                "descricao": item.get("descricao", ""),
                "unidade": item.get("unidade", "UN"),
                "quantidade": item.get("quantidade", 1),
                "valor": item.get("valor", 0),
                "tipo": "P",
                "origem": 0,
                "produto": {"id": item.get("produto", {}).get("id", 0)},
            })

        # Build transport with full etiqueta
        nfe_transporte = {
            "fretePorConta": transporte.get("fretePorConta", 0),
            "frete": transporte.get("frete", 0),
            "quantidadeVolumes": transporte.get("quantidadeVolumes", 1),
            "pesoBruto": transporte.get("pesoBruto", 0),
        }
        if etiqueta.get("nome") or etiqueta.get("endereco"):
            nfe_transporte["etiqueta"] = {
                "nome": etiqueta.get("nome") or nfe_contato["nome"],
                "endereco": etiqueta.get("endereco", ""),
                "numero": etiqueta.get("numero", ""),
                "complemento": etiqueta.get("complemento", ""),
                "municipio": etiqueta.get("municipio", ""),
                "uf": etiqueta.get("uf", ""),
                "cep": etiqueta.get("cep", ""),
                "bairro": etiqueta.get("bairro", ""),
            }

        nfe_payload = {
            "tipo": 1,
            "dataOperacao": now,
            "contato": nfe_contato,
            "itens": nfe_items,
            "parcelas": [
                {
                    "data": p.get("dataVencimento", ""),
                    "valor": p.get("valor", 0),
                    "formaPagamento": p.get("formaPagamento", {}),
                }
                for p in parcelas
            ],
            "transporte": nfe_transporte,
            "pedidoVenda": {"id": order_id},
        }

        if order.get("naturezaOperacao", {}).get("id"):
            nfe_payload["naturezaOperacao"] = {
                "id": order["naturezaOperacao"]["id"]
            }

        if order.get("loja", {}).get("id"):
            nfe_payload["loja"] = {"id": order["loja"]["id"]}

        # Use direct request to capture detailed error from Bling
        client = await self._get_client()
        await asyncio.sleep(RATE_LIMIT_DELAY)
        response = await client.post("/nfe", json=nfe_payload)

        if response.status_code == 401:
            await self._refresh_access_token()
            client = await self._get_client()
            response = await client.post("/nfe", json=nfe_payload)

        if response.status_code >= 400:
            try:
                err = response.json()
                error_info = err.get("error", err)
                fields = error_info.get("fields", [])
                msgs = [f.get("msg", "") for f in fields if f.get("msg")]
                detail = "; ".join(msgs) if msgs else error_info.get("message", response.text)
                raise ValueError(f"Bling: {detail}")
            except (ValueError,):
                raise
            except Exception:
                raise ValueError(f"Bling retornou erro {response.status_code}: {response.text}")

        data = response.json()
        nfe_result = data.get("data", data)

        # Auto-send to SEFAZ after creation
        nfe_id = nfe_result.get("id")
        if nfe_id:
            try:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                send_resp = await client.post(f"/nfe/{nfe_id}/enviar")
                if send_resp.status_code == 200:
                    send_data = send_resp.json().get("data", {})
                    xml_resp = send_data.get("xml", "")
                    if "cStat>100<" in xml_resp:
                        nfe_result["_sefaz"] = "autorizada"
                    elif "cStat" in xml_resp:
                        # Extract status message
                        import re
                        motivo = re.search(r"<xMotivo>(.*?)</xMotivo>", xml_resp)
                        nfe_result["_sefaz"] = motivo.group(1) if motivo else "processando"
                    else:
                        nfe_result["_sefaz"] = "enviada"
                else:
                    err_body = send_resp.json() if send_resp.status_code < 500 else {}
                    err_fields = err_body.get("error", {}).get("fields", [])
                    msgs = [f.get("msg", "") for f in err_fields if f.get("msg")]
                    nfe_result["_sefaz_erro"] = "; ".join(msgs) if msgs else "Erro ao enviar para SEFAZ"
            except Exception as e:
                nfe_result["_sefaz_erro"] = str(e)

        return nfe_result

    async def retry_nfe(self, nfe_id: int, order_id: int) -> dict:
        """Fix a pending NFe with correct data from the order and re-send to SEFAZ."""
        order = await self.get_order_detail(order_id)
        if not order:
            raise ValueError("Pedido nao encontrado")

        contato_pedido = order.get("contato", {})
        contato_id = contato_pedido.get("id", 0)
        itens = order.get("itens", [])
        parcelas = order.get("parcelas", [])
        transporte = order.get("transporte", {})
        etiqueta = transporte.get("etiqueta", {})

        # Fetch full contact
        contato_full = {}
        if contato_id:
            try:
                contato_full = await self.get_contato(contato_id)
            except Exception:
                pass

        end_geral = contato_full.get("endereco", {}).get("geral", {})

        # Get existing NFe to preserve numero
        existing = await self.get_nfe(nfe_id)
        numero = existing.get("numero", "")

        nfe_payload = {
            "tipo": 1,
            "numero": numero,
            "dataOperacao": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "contato": {
                "id": contato_id,
                "nome": contato_full.get("nome") or contato_pedido.get("nome", ""),
                "numeroDocumento": (
                    contato_full.get("numeroDocumento")
                    or contato_pedido.get("numeroDocumento", "")
                ).replace(".", "").replace("-", "").replace("/", ""),
                "tipo": contato_full.get("tipo") or contato_pedido.get("tipoPessoa", "F"),
                "indicadorIe": contato_full.get("indicadorIe", 9),
                "endereco": {
                    "endereco": etiqueta.get("endereco") or end_geral.get("endereco", ""),
                    "numero": etiqueta.get("numero") or end_geral.get("numero", ""),
                    "complemento": etiqueta.get("complemento") or end_geral.get("complemento", ""),
                    "bairro": etiqueta.get("bairro") or end_geral.get("bairro", ""),
                    "cep": etiqueta.get("cep") or end_geral.get("cep", ""),
                    "municipio": etiqueta.get("municipio") or end_geral.get("municipio", ""),
                    "uf": etiqueta.get("uf") or end_geral.get("uf", ""),
                },
            },
            "itens": [
                {
                    "codigo": item.get("codigo", ""),
                    "descricao": item.get("descricao", ""),
                    "unidade": item.get("unidade", "UN"),
                    "quantidade": item.get("quantidade", 1),
                    "valor": item.get("valor", 0),
                    "tipo": "P",
                    "origem": 0,
                    "produto": {"id": item.get("produto", {}).get("id", 0)},
                }
                for item in itens
            ],
            "parcelas": [
                {
                    "data": p.get("dataVencimento", ""),
                    "valor": p.get("valor", 0),
                    "formaPagamento": p.get("formaPagamento", {}),
                }
                for p in parcelas
            ],
            "transporte": {
                "fretePorConta": transporte.get("fretePorConta", 0),
                "frete": transporte.get("frete", 0),
                "etiqueta": {
                    "nome": etiqueta.get("nome") or contato_full.get("nome", ""),
                    "endereco": etiqueta.get("endereco", ""),
                    "numero": etiqueta.get("numero", ""),
                    "complemento": etiqueta.get("complemento", ""),
                    "municipio": etiqueta.get("municipio", ""),
                    "uf": etiqueta.get("uf", ""),
                    "cep": etiqueta.get("cep", ""),
                    "bairro": etiqueta.get("bairro", ""),
                },
            },
            "pedidoVenda": {"id": order_id},
        }

        if order.get("naturezaOperacao", {}).get("id"):
            nfe_payload["naturezaOperacao"] = {"id": order["naturezaOperacao"]["id"]}
        if order.get("loja", {}).get("id"):
            nfe_payload["loja"] = {"id": order["loja"]["id"]}

        # PUT to update the NFe with corrected data
        client = await self._get_client()
        await asyncio.sleep(RATE_LIMIT_DELAY)
        response = await client.put(f"/nfe/{nfe_id}", json=nfe_payload)

        if response.status_code == 401:
            await self._refresh_access_token()
            client = await self._get_client()
            response = await client.put(f"/nfe/{nfe_id}", json=nfe_payload)

        if response.status_code >= 400:
            err = response.json()
            fields = err.get("error", {}).get("fields", [])
            msgs = [f.get("msg", "") for f in fields if f.get("msg")]
            raise ValueError("Bling: " + ("; ".join(msgs) if msgs else err.get("error", {}).get("message", "")))

        result = response.json().get("data", {})

        # Send to SEFAZ
        await asyncio.sleep(RATE_LIMIT_DELAY)
        send_resp = await client.post(f"/nfe/{nfe_id}/enviar")
        if send_resp.status_code == 200:
            import re
            xml = send_resp.json().get("data", {}).get("xml", "")
            if "cStat>100<" in xml:
                result["_sefaz"] = "autorizada"
            else:
                motivo = re.search(r"<xMotivo>(.*?)</xMotivo>", xml)
                result["_sefaz"] = motivo.group(1) if motivo else "processando"
        else:
            err_body = send_resp.json() if send_resp.status_code < 500 else {}
            fields = err_body.get("error", {}).get("fields", [])
            msgs = [f.get("msg", "") for f in fields if f.get("msg")]
            result["_sefaz_erro"] = "; ".join(msgs) if msgs else "Erro ao enviar para SEFAZ"

        return result

    async def get_stock(self) -> dict[str, int]:
        """Returns dict of SKU -> stock quantity."""
        products = await self.get_products()
        return {p.sku: p.stock for p in products if p.sku}
