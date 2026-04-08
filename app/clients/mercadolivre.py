import httpx
import asyncio
from app.config import get_settings
from app.models.schemas import Product, Order

BASE_URL = "https://api.mercadolibre.com"
RATE_LIMIT_DELAY = 0.2  # ~5 requests/second


class MercadoLivreClient:
    def __init__(self):
        settings = get_settings()
        self.access_token = settings.ml_access_token
        self.refresh_token = settings.ml_refresh_token
        self.client_id = settings.ml_client_id
        self.client_secret = settings.ml_client_secret
        self.seller_id = settings.ml_seller_id
        self._client: httpx.AsyncClient | None = None

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/oauth/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self._client = None

    async def get_items(self) -> list[Product]:
        """Fetch all seller items with details."""
        products = []
        offset = 0
        limit = 50

        while True:
            search_data = await self._request(
                "GET",
                f"/users/{self.seller_id}/items/search",
                params={"offset": offset, "limit": limit},
            )

            item_ids = search_data.get("results", [])
            if not item_ids:
                break

            # Fetch details in batches of 20 (ML multiget limit)
            for i in range(0, len(item_ids), 20):
                batch = item_ids[i : i + 20]
                ids_str = ",".join(batch)
                items_data = await self._request(
                    "GET", "/items", params={"ids": ids_str}
                )

                for item_wrapper in items_data:
                    item = item_wrapper.get("body", {})
                    if item.get("status") != "active":
                        continue

                    sku = ""
                    for attr in item.get("attributes", []):
                        if attr.get("id") == "SELLER_SKU":
                            sku = attr.get("value_name", "")
                            break

                    if not sku:
                        sku = item.get("seller_custom_field", "") or ""

                    stock = item.get("available_quantity", 0)

                    products.append(
                        Product(
                            sku=sku,
                            name=item.get("title", ""),
                            price=float(item.get("price", 0)),
                            stock=stock,
                            source="ml",
                            external_id=item.get("id", ""),
                        )
                    )

            total = search_data.get("paging", {}).get("total", 0)
            offset += limit
            if offset >= total:
                break

        return products

    async def get_orders(
        self, date_from: str, date_to: str
    ) -> list[Order]:
        """Fetch orders in date range. Dates in ISO format: YYYY-MM-DD."""
        orders = []
        offset = 0
        limit = 50

        while True:
            data = await self._request(
                "GET",
                "/orders/search",
                params={
                    "seller": self.seller_id,
                    "order.date_created.from": f"{date_from}T00:00:00.000-00:00",
                    "order.date_created.to": f"{date_to}T23:59:59.999-00:00",
                    "offset": offset,
                    "limit": limit,
                },
            )

            results = data.get("results", [])
            if not results:
                break

            for item in results:
                orders.append(
                    Order(
                        order_id=str(item.get("id", "")),
                        date=item.get("date_created", ""),
                        total=float(item.get("total_amount", 0)),
                        status=item.get("status", ""),
                        items_count=len(item.get("order_items", [])),
                        source="ml",
                        buyer=item.get("buyer", {}).get("nickname", ""),
                    )
                )

            total = data.get("paging", {}).get("total", 0)
            offset += limit
            if offset >= total:
                break

        return orders

    async def get_stock(self) -> dict[str, int]:
        """Returns dict of SKU -> stock quantity."""
        items = await self.get_items()
        return {p.sku: p.stock for p in items if p.sku}
