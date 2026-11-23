from datetime import datetime
from decimal import Decimal

from powergym import parsear_movimiento

PAGO = [
    '19-11-2026<span class="tdEntrada"></span>  <span class="glyphicon glyphicon-question-sign tooltips" data-toggle="tooltip" data-placement="top"  title="ID: 72186\nFecha: 19-11-2026 18:16:19\nCreado: 19-11-2026 18:16:29\nActualizado: 19-11-2026 18:16:29"></span>',
    'Noviembre',
    '<a href="#" class="label" style="background-color: #000" data-toggle="tooltip" data-placement="top"  title="Recepcion">RE</a>',
    '<i>Efectivo</i>\n<span class="t_amount" >$ 32.000,00</span>',
    '<div class="dropdown"></div>',
]

CARGO = [
    '18-11-2026<span class="tdSalida"></span>  <span class="glyphicon tooltips" title="ID: 72185\nFecha: 18-11-2026 00:00:00\nCreado: 19-11-2026 18:12:06\nActualizado: 19-11-2026 18:12:06"></span>',
    '<strong>MUSCULACION 2026 [Noviembre 2026] Mensual (1)</strong> <span class="glyphicon tooltips" title="Cargo generado automáticamente"></span>',
    '<a href="#" class="label" title="Power Gym">PG</a>',
    '<span class="t_amount" data-toggle="tooltip" title="No representa un ingreso/egreso de dinero de Caja.">$ 32.000,00</span><i class="glyphicon glyphicon-tag discount-tag" data-toggle="tooltip" data-placement="top"  title="Perzonalizados Profe (-$ 8.000,00)"></i>',
    '<div></div>',
]


def test_pago():
    m = parsear_movimiento(PAGO)
    assert m.id == 72186 and m.es_pago
    assert m.fecha == datetime(2026, 11, 19, 18, 16, 19)
    assert m.detalle == "Noviembre"
    assert m.caja == "Recepcion"
    assert m.forma_pago == "Efectivo"
    assert m.monto == Decimal("32000.00")
    assert m.descuento is None


def test_cargo():
    m = parsear_movimiento(CARGO)
    assert m.id == 72185 and not m.es_pago
    assert m.detalle == "MUSCULACION 2026 [Noviembre 2026] Mensual (1)"
    assert m.forma_pago is None
    assert m.monto == Decimal("32000.00")
    assert m.descuento == "Perzonalizados Profe (-$ 8.000,00)"


def test_html_escapado():
    import html
    m = parsear_movimiento([html.escape(c) for c in PAGO])
    assert m.id == 72186 and m.monto == Decimal("32000.00")


# Datos inventados, con la misma forma que devuelve Power Gym.
ALUMNO = [
    '<a href="https://demo.sistemapowergym.com/users/1234/edit" class="userName tdEntrada">\n    <img class="circular_small" src="x.png" />\n    <span>\n        Juan Prueba        <i class=\'glyphicon glyphicon-tag\' title="Descuento: Algo"></i>            </span>\n</a>',
    'MUSCULACION 2026',
    '<span >\n    8 horas </span>\n<a href="javascript:void(0)" class="showEvents" data-user_id="1234"></a>',
    '<a class="t_amount" href="https://demo.sistemapowergym.com/account/view/1234">$ 4.600,00</a>',
    '<div class="userActions">\n<a class="btn sendWABtn" data-vars="{&quot;tel&quot;:&quot;1100000000&quot;,&quot;first_name&quot;:&quot;Juan&quot;,&quot;last_name&quot;:&quot;Prueba&quot;,&quot;t_amount&quot;:4600,&quot;last_visit_at&quot;:&quot;23\\/11\\/2026 12:08&quot;}">x</a>\n<a class="btn doLogin" data-dni="30111222" href="#">ok</a>\n</div>',
]


def test_alumno():
    from powergym import parsear_alumno
    a = parsear_alumno(ALUMNO)
    assert a.id == 1234
    assert a.dni == "30111222"
    assert a.nombre == "Juan Prueba"
    assert a.actividades == "MUSCULACION 2026"
    assert a.saldo == Decimal("4600.00")
    assert a.ultima_visita == datetime(2026, 11, 23, 12, 8)
    assert a.telefono == "1100000000"


def test_alumno_html_escapado():
    import html
    from powergym import parsear_alumno
    a = parsear_alumno([html.escape(c, quote=False) for c in ALUMNO])
    assert a.dni == "30111222" and a.ultima_visita == datetime(2026, 11, 23, 12, 8)
