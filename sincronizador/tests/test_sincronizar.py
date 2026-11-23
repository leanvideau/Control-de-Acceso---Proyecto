from datetime import datetime
from decimal import Decimal

from powergym import Alumno, Movimiento
from sincronizar import alumnos_a_revisar, pagos_nuevos


def alumno(id_, visita):
    return Alumno(id_, str(30000000 + id_), f"A{id_}", "MUSCULACION", Decimal(0), visita, None)


def mov(id_, fecha, pago=True):
    return Movimiento(id_, fecha, pago, "x", "Caja", "Efectivo" if pago else None, Decimal(1000), None)


class FakePG:
    def __init__(self, alumnos, movs):
        self.alumnos, self.movs = alumnos, movs

    def alumnos_por_ultima_visita(self, cantidad, inicio):
        return self.alumnos[inicio:inicio + cantidad]

    def movimientos(self, cuenta):
        return self.movs.get(cuenta, [])


def test_corta_en_la_ultima_corrida_y_filtra_pagos_viejos():
    d = datetime
    alumnos = [alumno(1, d(2026, 11, 23)), alumno(2, d(2026, 11, 22)), alumno(3, d(2026, 11, 10))]
    movs = {
        1: [mov(105, d(2026, 11, 23)), mov(104, d(2026, 11, 18), pago=False), mov(90, d(2026, 11, 1))],
        2: [mov(103, d(2026, 11, 21))],
        3: [mov(106, d(2026, 11, 22))],  # no vino: queda afuera
    }
    pg = FakePG(alumnos, movs)
    revisar = alumnos_a_revisar(pg, d(2026, 11, 20))
    assert [a.id for a in revisar] == [1, 2]
    nuevos = pagos_nuevos(pg, revisar, ultimo_id=100, desde=d(2026, 11, 20))
    assert [m.id for _, m in nuevos] == [103, 105]


def test_corrida_completa(tmp_path, monkeypatch):
    import json, sys
    import sincronizar
    from gymflow import Socio
    d = datetime.now()
    pg = FakePG([alumno(1, d)], {1: [mov(500, d)]})

    class FakeGF:
        def __init__(self, *a): pass
        def buscar_por_dni(self, dni): return Socio(9, dni, "A1", "Plan X", "active", "paid", None, False)

    (tmp_path / "config.json").write_text(json.dumps({"powergym_url": "u", "powergym_cookie": "c", "gymflow_token": "t"}))
    for nombre in ("CONFIG", "ESTADO", "REPORTE"):
        monkeypatch.setattr(sincronizar, nombre, tmp_path / getattr(sincronizar, nombre).name)
    monkeypatch.setattr(sincronizar, "PowerGym", lambda *a: pg)
    monkeypatch.setattr(sincronizar, "GymFlow", FakeGF)
    monkeypatch.setattr(sys, "argv", ["sincronizar.py"])
    sincronizar.main()
    reporte = (tmp_path / "pagos_nuevos.csv").read_text(encoding="utf-8-sig")
    assert "30000001" in reporte and "Plan X" in reporte
    assert json.loads((tmp_path / "estado.json").read_text())["ultimo_movimiento_id"] == 500
