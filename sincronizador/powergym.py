"""Lectura de datos del sistema viejo (Power Gym, versión web).

Power Gym no tiene API oficial: usamos las mismas llamadas que hace la página
(tablas DataTables) con la cookie de sesión `powergym_session`.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode

import requests

TAG_RE = re.compile(r"<[^>]+>")


def _texto(fragmento: str) -> str:
    """Saca las etiquetas HTML y deja solo el texto visible."""
    return " ".join(html.unescape(TAG_RE.sub(" ", fragmento)).split())


def _desescapar(celda: str) -> str:
    """Si la respuesta vino con el HTML escapado una vez de más (copiada del navegador
    o del chat), lo deja como lo manda el servidor."""
    return html.unescape(celda) if "&lt;" in celda else celda


def _monto(texto: str) -> Decimal | None:
    """'$ 32.000,00' -> Decimal('32000.00')."""
    m = re.search(r"\$\s*(-?[\d.]+,\d{2})", texto)
    if not m:
        return None
    return Decimal(m.group(1).replace(".", "").replace(",", "."))


@dataclass
class Movimiento:
    id: int
    fecha: datetime
    es_pago: bool          # True = pago del alumno (entrada de caja); False = cargo de cuota
    detalle: str           # "Noviembre", "MUSCULACION 2026 [Noviembre 2026] Mensual (1)", ...
    caja: str              # quién/dónde se registró: "Caja Central", "Power Gym", ...
    forma_pago: str | None # "Efectivo", "Transferencia", ... (solo pagos)
    monto: Decimal | None
    descuento: str | None  # ej. "Perzonalizados Profe (-$ 8.000,00)" (solo cargos)


def parsear_movimiento(fila: list[str]) -> Movimiento:
    """Convierte una fila de /api/inouts/{cuenta} en un Movimiento."""
    fila = [_desescapar(c) for c in fila]
    col_fecha, col_detalle, col_caja, col_monto = fila[0], fila[1], fila[2], fila[3]

    id_ = int(re.search(r"ID:\s*(\d+)", col_fecha).group(1))
    fecha_txt = re.search(r"Fecha:\s*([\d-]+ [\d:]+)", col_fecha).group(1)
    fecha = datetime.strptime(fecha_txt, "%d-%m-%Y %H:%M:%S")
    es_pago = "tdEntrada" in col_fecha

    caja_m = re.search(r'title="([^"]*)"', col_caja)
    caja = caja_m.group(1) if caja_m else _texto(col_caja)

    forma_m = re.search(r"<i>([^<]+)</i>", col_monto)
    monto_m = re.search(r'class="t_amount"[^>]*>([^<]+)<', col_monto)
    desc_m = re.search(r'discount-tag"[^>]*title="([^"]*)"', col_monto)

    return Movimiento(
        id=id_,
        fecha=fecha,
        es_pago=es_pago,
        detalle=_texto(col_detalle),
        caja=caja,
        forma_pago=forma_m.group(1).strip() if forma_m else None,
        monto=_monto(monto_m.group(1)) if monto_m else None,
        descuento=desc_m.group(1) if desc_m else None,
    )


@dataclass
class Alumno:
    id: int                      # número de cuenta en Power Gym (/users/{id})
    dni: str | None
    nombre: str
    actividades: str             # "MUSCULACION 2026", "Sin Actividades", ...
    saldo: Decimal | None        # lo que debe (cuenta corriente)
    ultima_visita: datetime | None
    telefono: str | None


def parsear_alumno(fila: list[str]) -> Alumno:
    """Convierte una fila de /user/api_datatable en un Alumno."""
    fila = [_desescapar(c) for c in fila]
    col_nombre, col_act, _col_visita, col_saldo, col_acciones = fila[:5]

    id_ = int(re.search(r"/users/(\d+)", col_nombre).group(1))
    nombre_m = re.search(r"<span>(.*?)(?:<i|</span>)", col_nombre, re.S)
    dni_m = re.search(r'data-dni="([^"]*)"', col_acciones)

    datos = {}
    vars_m = re.search(r'data-vars="([^"]*)"', col_acciones)
    if vars_m:
        try:
            datos = json.loads(html.unescape(vars_m.group(1)))
        except ValueError:
            datos = {}
    visita = None
    if datos.get("last_visit_at"):
        visita = datetime.strptime(datos["last_visit_at"], "%d/%m/%Y %H:%M")

    return Alumno(
        id=id_,
        dni=(dni_m.group(1).strip() or None) if dni_m else None,
        nombre=" ".join(nombre_m.group(1).split()) if nombre_m else "",
        actividades=_texto(col_act),
        saldo=_monto(_texto(col_saldo)),
        ultima_visita=visita,
        telefono=datos.get("tel") or None,
    )


def _params_datatable(columnas: int, inicio: int, cantidad: int, orden_col: int) -> dict:
    p = {
        "sEcho": 1,
        "iColumns": columnas,
        "sColumns": "," * (columnas - 1),
        "iDisplayStart": inicio,
        "iDisplayLength": cantidad,
        "sSearch": "",
        "bRegex": "false",
        "iSortCol_0": orden_col,
        "sSortDir_0": "desc",
        "iSortingCols": 1,
    }
    for i in range(columnas):
        p.update({
            f"mDataProp_{i}": i,
            f"sSearch_{i}": "",
            f"bRegex_{i}": "false",
            f"bSearchable_{i}": "true",
            f"bSortable_{i}": "true",
        })
    return p


class PowerGym:
    def __init__(self, base_url: str, cookie_sesion: str):
        self.base = base_url.rstrip("/")
        self.http = requests.Session()
        self.http.cookies.set("powergym_session", cookie_sesion)
        self.http.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        })

    def _get(self, ruta: str, params: dict, referer: str) -> dict:
        r = self.http.get(f"{self.base}{ruta}?{urlencode(params)}",
                          headers={"Referer": f"{self.base}{referer}"}, timeout=30)
        r.raise_for_status()
        if "json" not in r.headers.get("Content-Type", ""):
            raise RuntimeError("Power Gym no devolvió datos: probablemente venció la sesión.")
        return r.json()

    def alumnos_por_ultima_visita(self, cantidad: int = 100, inicio: int = 0) -> list[Alumno]:
        """Lista de alumnos ordenada por última visita (más reciente primero).

        Ojo: la tabla ordena por la última asistencia, no por el último pago.
        """
        datos = self._get("/user/api_datatable",
                          _params_datatable(5, inicio, cantidad, orden_col=2), "/user")
        return [parsear_alumno(f) for f in datos["aaData"]]

    def movimientos(self, cuenta: int, cantidad: int = 50) -> list[Movimiento]:
        params = _params_datatable(5, 0, cantidad, orden_col=0)
        params["future"] = "false"
        datos = self._get(f"/api/inouts/{cuenta}", params, f"/account/view/{cuenta}")
        return [parsear_movimiento(f) for f in datos["aaData"]]
