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


CONFIG = {"powergym_url": "u", "powergym_cookie": "c", "gymflow_token": "t",
          "cash_shift_id": 3296,
          "planes": {"MUSCULACION": {"plan_id": 1751, "meses": 1}},
          "formas_pago": {"Efectivo": 843}}


def _correr(tmp_path, monkeypatch, socio_vence, argv):
    import json, sys
    import sincronizar
    from gymflow import Socio
    d = datetime.now()
    pg = FakePG([alumno(1, d)], {1: [mov(500, d)]})
    posts = []

    class FakeGF:
        def __init__(self, *a): pass
        def buscar_por_dni(self, dni): return Socio(9, dni, "A1", "Plan X", "active", "paid", socio_vence, False)
        def crear_membresia(self, datos): posts.append(datos); return {"ok": True}

    (tmp_path / "config.json").write_text(json.dumps(CONFIG))
    monkeypatch.setattr(sincronizar, "CONFIG", tmp_path / "config.json")
    monkeypatch.setattr(sincronizar, "ESTADO", tmp_path / "estado.json")
    monkeypatch.setattr(sincronizar, "REPORTES", tmp_path / "reportes")
    monkeypatch.setattr(sincronizar, "PowerGym", lambda *a: pg)
    monkeypatch.setattr(sincronizar, "GymFlow", FakeGF)
    monkeypatch.setattr(sys, "argv", ["sincronizar.py", *argv])
    sincronizar.main()
    reporte = next((tmp_path / "reportes").iterdir()).read_text(encoding="utf-8-sig")
    return posts, reporte


def test_modo_prueba_no_carga(tmp_path, monkeypatch):
    posts, reporte = _correr(tmp_path, monkeypatch, None, [])
    assert posts == [] and "Se cargaría" in reporte and "30000001" in reporte
    assert not (tmp_path / "estado.json").exists()


def test_carga_y_no_repite(tmp_path, monkeypatch):
    import json, shutil
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"])
    assert len(posts) == 1 and posts[0]["plan_id"] == "1751" and posts[0]["member_id"] == 9
    assert posts[0]["cash_payment_method_id"] == 843 and posts[0]["amount_paid"] == "1000.00"
    assert "CARGADO" in reporte
    assert json.loads((tmp_path / "estado.json").read_text())["ultimo_movimiento_id"] == 500
    shutil.rmtree(tmp_path / "reportes")
    posts2, _ = _correr(tmp_path, monkeypatch, None, ["--cargar"])
    assert posts2 == []


def test_no_carga_si_ya_vigente(tmp_path, monkeypatch):
    from datetime import date, timedelta
    posts, reporte = _correr(tmp_path, monkeypatch, date.today() + timedelta(days=10), ["--cargar"])
    assert posts == [] and "ya está vigente" in reporte
