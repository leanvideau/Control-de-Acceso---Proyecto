"""Acceso al sistema nuevo (GymFlow) con la cookie de sesión web `gf_token`.

GymFlow no tiene API pública: usamos las mismas llamadas que hace su página.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import requests


@dataclass
class Socio:
    id: int
    dni: str
    nombre: str
    plan: str | None
    estado_membresia: str | None   # "active", ...
    estado_pago: str | None        # "paid", ...
    vence: date | None
    debe: bool


def parsear_socio(d: dict) -> Socio:
    vence = None
    if d.get("end_date"):
        vence = date.fromisoformat(d["end_date"])
    return Socio(
        id=int(d["id"]),
        dni=str(d.get("dni") or "").strip(),
        nombre=d.get("name") or "",
        plan=d.get("plan_name"),
        estado_membresia=d.get("membership_status"),
        estado_pago=d.get("payment_status"),
        vence=vence,
        debe=bool(d.get("has_debt")),
    )


class GymFlow:
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.http = requests.Session()
        self.http.cookies.set("gf_token", token)
        self.http.headers["Accept"] = "*/*"

    def buscar_por_dni(self, dni: str) -> Socio | None:
        r = self.http.get(
            f"{self.base}/api/members.php",
            params={"q": dni, "status": "all", "sort": "name", "dir": "asc",
                    "page": 1, "with_bajas": 1, "with_last_access": 1},
            headers={"Referer": f"{self.base}/pages/admin/members.php"},
            timeout=30,
        )
        r.raise_for_status()
        if "json" not in r.headers.get("Content-Type", ""):
            raise RuntimeError("GymFlow no devolvió datos: probablemente venció la sesión.")
        # La búsqueda es por texto: nos quedamos solo con el DNI exacto.
        for m in r.json().get("members", []):
            socio = parsear_socio(m)
            if socio.dni == dni:
                return socio
        return None
