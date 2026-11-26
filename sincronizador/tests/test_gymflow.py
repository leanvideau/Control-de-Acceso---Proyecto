from datetime import date

from gymflow import parsear_socio

# Datos inventados con la forma de /api/members.php
RESP = {"id": 1, "name": "Juan Prueba", "dni": "30111222", "active": 1,
        "end_date": "2026-12-20", "payment_status": "paid", "has_debt": 0,
        "plan_name": "Musculación", "membership_status": "active"}


def test_socio():
    s = parsear_socio(RESP)
    assert s.dni == "30111222" and s.plan == "Musculación"
    assert s.vence == date(2026, 12, 20) and not s.debe and s.estado_pago == "paid"
