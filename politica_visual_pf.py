"""Decisión única de fotos Rockstar y control PF-41.

Compartida por el renderizador y el control de calidad para evitar que el
primero omita un informe que el segundo exige.
"""
def modo_rockstar(tema_id, bandera):
    if not isinstance(tema_id, str):
        return False
    return str(bandera).strip() == "1" and tema_id.startswith(
        ("gta6", "historia-gtavi-")
    )

def requiere_informe_pf41(plan, formato, bandera):
    return (formato == "short"
            and plan.get("estilo_retencion") ==
                "PF-41-ganchos-directos-planos-3s"
            and modo_rockstar(plan.get("tema_id"), bandera))
