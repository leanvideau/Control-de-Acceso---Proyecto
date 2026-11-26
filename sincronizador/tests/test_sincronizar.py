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
          "planes": [{"powergym": ["MUSCULACION"], "plan_id": 1751, "dias": 30}],
          "formas_pago": {"Efectivo": 843}}


def _correr(tmp_path, monkeypatch, socio_vence, argv, respuesta="s", config=None):
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

    (tmp_path / "config.json").write_text(json.dumps(config or CONFIG))
    monkeypatch.setattr(sincronizar, "CONFIG", tmp_path / "config.json")
    monkeypatch.setattr(sincronizar, "ESTADO", tmp_path / "estado.json")
    monkeypatch.setattr(sincronizar, "REPORTES", tmp_path / "reportes")
    monkeypatch.setattr(sincronizar, "PowerGym", lambda *a: pg)
    monkeypatch.setattr(sincronizar, "GymFlow", FakeGF)
    monkeypatch.setattr(sys, "argv", ["sincronizar.py", *argv])
    respuestas = list(respuesta) if isinstance(respuesta, list) else None
    monkeypatch.setattr("builtins.input",
                        lambda *_: respuestas.pop(0) if respuestas is not None else respuesta)
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
    assert "CARGADO" in reporte and "cash_shift_id" not in posts[0]
    from datetime import date, timedelta
    assert posts[0]["end_date"] == (date.today() + timedelta(days=30)).isoformat()
    assert json.loads((tmp_path / "estado.json").read_text())["ultimo_movimiento_id"] == 500
    shutil.rmtree(tmp_path / "reportes")
    posts2, _ = _correr(tmp_path, monkeypatch, None, ["--cargar"])
    assert posts2 == []


def test_no_carga_si_ya_vigente(tmp_path, monkeypatch):
    from datetime import date, timedelta
    posts, reporte = _correr(tmp_path, monkeypatch, date.today() + timedelta(days=10), ["--cargar"])
    assert posts == [] and "ya está vigente" in reporte


def test_si_digo_que_no_no_carga(tmp_path, monkeypatch):
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta="n")
    assert posts == [] and "dijiste que no" in reporte


def _alumno_sin_actividad(monkeypatch):
    import sincronizar
    monkeypatch.setattr(sincronizar, "alumnos_a_revisar",
                        lambda pg, desde: [Alumno(1, "30000001", "A1", "Sin Actividades", Decimal(0), datetime.now(), None)])


def test_sin_actividad_pregunta_plan(tmp_path, monkeypatch):
    _alumno_sin_actividad(monkeypatch)
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta=["1", "s"])
    assert len(posts) == 1 and posts[0]["plan_id"] == "1751"


def test_sin_actividad_elige_plan_pero_dice_que_no(tmp_path, monkeypatch):
    _alumno_sin_actividad(monkeypatch)
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta=["1", "n"])
    assert posts == [] and "dijiste que no" in reporte


def test_sin_actividad_elige_no_cargar(tmp_path, monkeypatch):
    _alumno_sin_actividad(monkeypatch)
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta="0")
    assert posts == [] and "elegiste no cargarlo" in reporte


def test_sin_actividad_modo_prueba(tmp_path, monkeypatch):
    _alumno_sin_actividad(monkeypatch)
    posts, reporte = _correr(tmp_path, monkeypatch, None, [])
    assert posts == [] and "Te va a preguntar" in reporte


def test_los_que_no_estan_van_a_archivo_aparte(tmp_path, monkeypatch):
    import json, sys
    import sincronizar
    d = datetime.now()
    pg = FakePG([alumno(1, d)], {1: [mov(500, d)]})

    class FakeGF:
        def __init__(self, *a): pass
        def buscar_por_dni(self, dni): return None
        def crear_membresia(self, datos): raise AssertionError("no debería cargar")

    (tmp_path / "config.json").write_text(json.dumps(CONFIG))
    monkeypatch.setattr(sincronizar, "CONFIG", tmp_path / "config.json")
    monkeypatch.setattr(sincronizar, "ESTADO", tmp_path / "estado.json")
    monkeypatch.setattr(sincronizar, "REPORTES", tmp_path / "reportes")
    monkeypatch.setattr(sincronizar, "PowerGym", lambda *a: pg)
    monkeypatch.setattr(sincronizar, "GymFlow", FakeGF)
    monkeypatch.setattr(sys, "argv", ["sincronizar.py"])
    sincronizar.main()
    archivos = {p.name.split("_2")[0]: p for p in (tmp_path / "reportes").iterdir()}
    agregar = archivos["alumnos_para_agregar"].read_text(encoding="utf-8-sig")
    assert "30000001" in agregar and "Musculación" not in agregar  # plan sin nombre en CONFIG de test
    assert "1751" in agregar


def test_forma_otro_pregunta(tmp_path, monkeypatch):
    import sincronizar
    pago_otro = Movimiento(500, datetime.now(), True, "x", "Caja", "Otro", Decimal(1000), None)
    monkeypatch.setattr(sincronizar, "pagos_nuevos", lambda pg, al, u, d: [(al[0], pago_otro)])
    conf = dict(CONFIG, formas_pago={"Efectivo": 843, "Transferencia": 846, "Otro": None})
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta=["2", "s"], config=conf)
    assert len(posts) == 1 and posts[0]["cash_payment_method_id"] == 846


def test_forma_otro_elige_no_cargar(tmp_path, monkeypatch):
    import sincronizar
    pago_otro = Movimiento(500, datetime.now(), True, "x", "Caja", "Otro", Decimal(1000), None)
    monkeypatch.setattr(sincronizar, "pagos_nuevos", lambda pg, al, u, d: [(al[0], pago_otro)])
    posts, reporte = _correr(tmp_path, monkeypatch, None, ["--cargar"], respuesta=["0"])
    assert posts == [] and "elegiste no cargarlo" in reporte
