from typing import Optional

from app.models.schemas import StockItem


def compare_stock(
    bling_stock: dict[str, int], ml_stock: dict[str, int],
    bling_names: Optional[dict[str, str]] = None,
) -> dict:
    """Compare stock levels between Bling and ML.

    Args:
        bling_stock: SKU -> quantity from Bling
        ml_stock: SKU -> quantity from ML
        bling_names: SKU -> product name (optional, for display)
    """
    if bling_names is None:
        bling_names = {}

    all_skus = set(bling_stock.keys()) | set(ml_stock.keys())
    items: list[StockItem] = []
    divergent = 0
    synced = 0

    for sku in sorted(all_skus):
        qty_bling = bling_stock.get(sku, 0)
        qty_ml = ml_stock.get(sku, 0)
        diff = qty_bling - qty_ml

        items.append(
            StockItem(
                sku=sku,
                name=bling_names.get(sku, sku),
                stock_bling=qty_bling,
                stock_ml=qty_ml,
                difference=diff,
            )
        )

        if diff != 0:
            divergent += 1
        else:
            synced += 1

    # Top divergences by absolute difference
    items_sorted = sorted(items, key=lambda x: abs(x.difference), reverse=True)

    zero_bling_only = sum(
        1 for i in items if i.stock_bling == 0 and i.stock_ml > 0
    )
    zero_ml_only = sum(
        1 for i in items if i.stock_ml == 0 and i.stock_bling > 0
    )

    return {
        "total_skus": len(all_skus),
        "synced": synced,
        "divergent": divergent,
        "zero_only_bling": zero_bling_only,
        "zero_only_ml": zero_ml_only,
        "items": [i.model_dump() for i in items_sorted],
    }
