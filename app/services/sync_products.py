from app.models.schemas import Product, ProductDivergence


def compare_products(
    bling_products: list[Product], ml_products: list[Product]
) -> dict:
    bling_by_sku = {p.sku: p for p in bling_products if p.sku}
    ml_by_sku = {p.sku: p for p in ml_products if p.sku}

    all_skus = set(bling_by_sku.keys()) | set(ml_by_sku.keys())
    divergences: list[ProductDivergence] = []
    synced = 0

    for sku in all_skus:
        b = bling_by_sku.get(sku)
        m = ml_by_sku.get(sku)

        if b and not m:
            divergences.append(
                ProductDivergence(
                    sku=sku,
                    name=b.name,
                    field="missing",
                    value_bling="Presente",
                    value_ml="Ausente",
                    severity="error",
                )
            )
            continue

        if m and not b:
            divergences.append(
                ProductDivergence(
                    sku=sku,
                    name=m.name,
                    field="missing",
                    value_bling="Ausente",
                    value_ml="Presente",
                    severity="error",
                )
            )
            continue

        has_divergence = False

        if abs(b.price - m.price) > 0.01:
            divergences.append(
                ProductDivergence(
                    sku=sku,
                    name=b.name,
                    field="price",
                    value_bling=f"R$ {b.price:.2f}",
                    value_ml=f"R$ {m.price:.2f}",
                    severity="warning",
                )
            )
            has_divergence = True

        if b.name.strip().lower() != m.name.strip().lower():
            divergences.append(
                ProductDivergence(
                    sku=sku,
                    name=b.name,
                    field="name",
                    value_bling=b.name,
                    value_ml=m.name,
                    severity="info",
                )
            )
            has_divergence = True

        if not has_divergence:
            synced += 1

    missing_ml = sum(1 for d in divergences if d.field == "missing" and d.value_ml == "Ausente")
    missing_bling = sum(1 for d in divergences if d.field == "missing" and d.value_bling == "Ausente")

    return {
        "total_bling": len(bling_by_sku),
        "total_ml": len(ml_by_sku),
        "synced": synced,
        "divergent": len(set(d.sku for d in divergences)),
        "missing_ml": missing_ml,
        "missing_bling": missing_bling,
        "divergences": [d.model_dump() for d in divergences],
    }
