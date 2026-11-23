"""Decide qué membresía cargar en GymFlow a partir de un pago de Power Gym."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from gymflow import Socio
from powergym import Alumno, Movimiento


def sumar_meses(d: date, meses: int) -> date:
    m = d.month - 1 + meses
    anio, mes = d.year + m // 12, m % 12 + 1
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1]))


@dataclass
class Decision:
    datos: dict | None   # lo que se mandaría a GymFlow; None = hay que hacerlo a mano
    motivo: str          # explicación para el reporte


def decidir(alumno: Alumno, pago: Movimiento, socio: Socio | None, config: dict) -> Decision:
    if not alumno.dni:
        return Decision(None, "Manual: el alumno no tiene DNI en Power Gym")
    if socio is None:
        return Decision(None, "Manual: no está en GymFlow")

    plan = config.get("planes", {}).get(alumno.actividades)
    if not plan:
        return Decision(None, f"Manual: falta equivalencia de plan para '{alumno.actividades}'")

    forma_id = config.get("formas_pago", {}).get(pago.forma_pago or "")
    if not forma_id:
        return Decision(None, f"Manual: falta equivalencia de forma de pago '{pago.forma_pago}'")

    if not pago.monto or pago.monto <= 0:
        return Decision(None, "Manual: el pago no tiene monto")

    inicio = pago.fecha.date()
    if socio.vence and socio.vence >= inicio:
        return Decision(None, f"Manual: en GymFlow ya está vigente hasta {socio.vence:%d/%m/%Y}")

    fin = sumar_meses(inicio, int(plan.get("meses", 1)))
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
        "cash_shift_id": int(config["cash_shift_id"]),
        "all_sedes": 1,
    }
    return Decision(datos, f"Cargar plan {plan['plan_id']} del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y} por $ {monto}")
