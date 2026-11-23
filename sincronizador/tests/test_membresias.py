from datetime import date

from membresias import sumar_meses


def test_sumar_meses():
    assert sumar_meses(date(2026, 11, 23), 1) == date(2026, 12, 23)
    assert sumar_meses(date(2026, 12, 15), 1) == date(2027, 1, 15)
    assert sumar_meses(date(2027, 1, 31), 1) == date(2027, 2, 28)
