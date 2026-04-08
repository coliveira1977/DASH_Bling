from app.models.schemas import Order, OrderDivergence

# Mapeamento de status ML -> Bling equivalente
ML_STATUS_MAP = {
    "paid": "em aberto",
    "shipped": "atendido",
    "delivered": "atendido",
    "cancelled": "cancelado",
}


def compare_orders(
    bling_orders: list[Order], ml_orders: list[Order]
) -> dict:
    bling_by_id = {o.order_id: o for o in bling_orders}
    ml_by_id = {o.order_id: o for o in ml_orders}

    divergences: list[OrderDivergence] = []
    synced = 0

    # Check ML orders against Bling
    for order_id, ml_order in ml_by_id.items():
        b_order = bling_by_id.get(order_id)

        if not b_order:
            divergences.append(
                OrderDivergence(
                    order_id=order_id,
                    date=str(ml_order.date),
                    field="missing",
                    value_bling="Ausente",
                    value_ml=f"Presente ({ml_order.status})",
                    severity="error",
                )
            )
            continue

        has_divergence = False

        if abs(b_order.total - ml_order.total) > 0.01:
            divergences.append(
                OrderDivergence(
                    order_id=order_id,
                    date=str(ml_order.date),
                    field="total",
                    value_bling=f"R$ {b_order.total:.2f}",
                    value_ml=f"R$ {ml_order.total:.2f}",
                    severity="warning",
                )
            )
            has_divergence = True

        ml_status_normalized = ML_STATUS_MAP.get(
            ml_order.status.lower(), ml_order.status.lower()
        )
        bling_status_normalized = b_order.status.lower()

        if ml_status_normalized != bling_status_normalized:
            divergences.append(
                OrderDivergence(
                    order_id=order_id,
                    date=str(ml_order.date),
                    field="status",
                    value_bling=b_order.status,
                    value_ml=ml_order.status,
                    severity="warning",
                )
            )
            has_divergence = True

        if not has_divergence:
            synced += 1

    # Check Bling orders not in ML
    for order_id, b_order in bling_by_id.items():
        if order_id not in ml_by_id:
            divergences.append(
                OrderDivergence(
                    order_id=order_id,
                    date=str(b_order.date),
                    field="missing",
                    value_bling=f"Presente ({b_order.status})",
                    value_ml="Ausente",
                    severity="info",
                )
            )

    return {
        "total_bling": len(bling_by_id),
        "total_ml": len(ml_by_id),
        "synced": synced,
        "divergent": len(set(d.order_id for d in divergences)),
        "missing_in_bling": sum(1 for d in divergences if d.field == "missing" and d.value_bling == "Ausente"),
        "missing_in_ml": sum(1 for d in divergences if d.field == "missing" and d.value_ml == "Ausente"),
        "divergences": [d.model_dump() for d in divergences],
    }
