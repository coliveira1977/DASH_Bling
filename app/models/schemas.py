from pydantic import BaseModel
from datetime import datetime


class Product(BaseModel):
    sku: str
    name: str
    price: float
    stock: int
    source: str  # "bling" ou "ml"
    external_id: str = ""


class Order(BaseModel):
    order_id: str
    date: datetime
    total: float
    status: str
    items_count: int
    source: str
    buyer: str = ""


class StockItem(BaseModel):
    sku: str
    name: str
    stock_bling: int = 0
    stock_ml: int = 0
    difference: int = 0


class ProductDivergence(BaseModel):
    sku: str
    name: str
    field: str  # "price", "name", "missing"
    value_bling: str = ""
    value_ml: str = ""
    severity: str = "warning"  # "warning", "error", "info"


class OrderDivergence(BaseModel):
    order_id: str
    date: str
    field: str  # "status", "total", "missing"
    value_bling: str = ""
    value_ml: str = ""
    severity: str = "warning"


class SyncSummary(BaseModel):
    total_products_bling: int = 0
    total_products_ml: int = 0
    products_synced: int = 0
    products_divergent: int = 0
    products_missing_ml: int = 0
    products_missing_bling: int = 0
    total_orders_bling: int = 0
    total_orders_ml: int = 0
    orders_synced: int = 0
    orders_divergent: int = 0
    stock_divergent: int = 0
    stock_synced: int = 0
    health_percentage: float = 0.0
    last_check: str = ""
