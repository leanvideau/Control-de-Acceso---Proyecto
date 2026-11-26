from membresias import actividades_de, buscar_plan

PLANES = [
    {"powergym": ["MUSCULACION 2026"], "plan_id": 1751},
    {"powergym": ["MUSCULACION 2026", "Yoga Integral - Lunes y Miercoles 9.30 hs"], "plan_id": 1763},
]


def test_combo_sin_importar_orden_ni_tildes():
    assert buscar_plan("Yoga Integral - Lunes y Miércoles 9.30 hs, MUSCULACION 2026", PLANES)["plan_id"] == 1763
    assert buscar_plan("MUSCULACION 2026", PLANES)["plan_id"] == 1751


def test_sin_equivalencia():
    assert buscar_plan("SQUASH", PLANES) is None
    assert buscar_plan("Sin Actividades", PLANES) is None


def test_config_ejemplo_es_valida():
    import json, pathlib
    c = json.loads((pathlib.Path(__file__).parent.parent / "config.ejemplo.json").read_text(encoding="utf-8"))
    assert buscar_plan("MUSCULACION 2026", c["planes"])["plan_id"] == 1751
    assert actividades_de("a, b") == actividades_de("B,A")
