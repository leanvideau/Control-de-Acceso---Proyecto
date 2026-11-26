"""Decide qué membresía cargar en GymFlow a partir de un pago de Power Gym."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta

from gymflow import Socio
from powergym import Alumno, Movimiento


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.upper().replace("/", " ").split())


def actividades_de(texto: str) -> frozenset[str]:
    """'MUSCULACION 2026, Yoga Integral - ...' -> conjunto normalizado (el orden no importa)."""
    return frozenset(_normalizar(a) for a in texto.split(",") if a.strip())


def buscar_plan(actividades: str, planes: list[dict]) -> dict | None:
    """Busca el plan de GymFlow cuyo grupo de actividades de Power Gym coincide exacto."""
    clave = actividades_de(actividades)
    for plan in planes:
        if actividades_de(", ".join(plan["powergym"])) == clave:
            return plan
    return None


@dataclass
class Decision:
    datos: dict | None   # lo que se mandaría a GymFlow; None = hay que hacerlo a mano
    motivo: str          # explicación para el reporte
    falta_plan: bool = False   # True = falta el plan: se le puede preguntar a Lean
    falta_forma: bool = False  # True = falta la forma de pago ("Otro"): se le puede preguntar


def planes_gymflow(config: dict) -> list[dict]:
    """Planes de GymFlow de la tabla, sin repetir, para elegir a mano."""
    vistos, lista = set(), []
    for p in config.get("planes", []):
        if p.get("plan_id") and p["plan_id"] not in vistos:
            vistos.add(p["plan_id"])
            lista.append(p)
    return lista


def formas_gymflow(config: dict) -> list[tuple[str, int]]:
    """Formas de pago de GymFlow (nombre, id) sin repetir, para elegir a mano."""
    vistos, lista = set(), []
    for nombre, id_ in config.get("formas_pago", {}).items():
        if id_ and id_ not in vistos:
            vistos.add(id_)
            lista.append((nombre, int(id_)))
    return lista


def decidir(alumno: Alumno, pago: Movimiento, socio: Socio | None, config: dict,
            plan: dict | None = None, forma_id: int | None = None) -> Decision:
    """`plan` y `forma_id` permiten forzarlos (cuando Lean los elige a mano)."""
    if not alumno.dni:
        return Decision(None, "Manual: el alumno no tiene DNI en Power Gym")
    if socio is None:
        return Decision(None, "Manual: no está en GymFlow")

    if not pago.monto or pago.monto <= 0:
        return Decision(None, "Manual: el pago no tiene monto")

    inicio = pago.fecha.date()
    if socio.vence and socio.vence >= inicio:
        return Decision(None, f"Manual: en GymFlow ya está vigente hasta {socio.vence:%d/%m/%Y}")

    if plan is None:
        plan = buscar_plan(alumno.actividades, config.get("planes", []))
    if not plan or not plan.get("plan_id"):
        return Decision(None, f"Elegir plan: en Power Gym figura '{alumno.actividades}'",
                        falta_plan=True)

    if forma_id is None:
        forma_id = config.get("formas_pago", {}).get(pago.forma_pago or "")
    if not forma_id:
        return Decision(None, f"Elegir forma de pago: en Power Gym figura '{pago.forma_pago or 'sin forma'}'",
                        falta_forma=True)

    fin = inicio + timedelta(days=int(plan.get("dias", 30)))
    monto = f"{pago.monto:.2f}"
    datos = {
        "day_pass": "",
        "plan_id": str(plan["plan_id"]),
        "start_date": inicio.isoformat(),
        "end_date": fin.isoformat(),
        "align_with_membership_id": "",
        "amount_due": monto,
        "amount_paid": monto,
        "notes": f"Importado de Power Gym (mov. {pago.id}: {pago.detalle})",
        "member_id": socio.id,
        "cash_payment_method_id": int(forma_id),
        "all_sedes": 1,
    }
    if config.get("cash_shift_id"):
        datos["cash_shift_id"] = int(config["cash_shift_id"])
    return Decision(datos, f"Cargar '{plan.get('nombre', plan['plan_id'])}' del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y} por $ {monto}")
