"""Busca los pagos nuevos en Power Gym desde la última corrida.

Por ahora genera un reporte (pagos_nuevos.csv) con lo que hay que pasar a GymFlow,
y al lado cómo está ese alumno hoy en GymFlow (plan, vencimiento, si debe).
Cuando tengamos las llamadas de GymFlow, este mismo programa los va a cargar solo.

Uso:
    python sincronizar.py            # busca pagos desde la última corrida
    python sincronizar.py --dias 10  # primera vez: mira los últimos 10 días

Configuración en config.json (NO subirlo a ningún lado, tiene la sesión):
    {"powergym_url": "https://laroca.sistemapowergym.com",
     "powergym_cookie": "valor de powergym_session",
     "gymflow_url": "https://sistema.gymflow.com.ar",
     "gymflow_token": "valor de gf_token"}
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from gymflow import GymFlow
from powergym import Alumno, Movimiento, PowerGym

CARPETA = Path(__file__).parent
CONFIG = CARPETA / "config.json"
ESTADO = CARPETA / "estado.json"
REPORTE = CARPETA / "pagos_nuevos.csv"

# La lista de Power Gym ordena por última visita, no por último pago. Un alumno puede
# pagar sin venir ese día, así que miramos un margen extra hacia atrás.
MARGEN = timedelta(days=3)
POR_PAGINA = 100


def leer_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {}


def alumnos_a_revisar(pg: PowerGym, desde: datetime) -> list[Alumno]:
    """Alumnos que vinieron desde `desde` (la lista viene de más reciente a más vieja)."""
    resultado, inicio = [], 0
    while True:
        pagina = pg.alumnos_por_ultima_visita(POR_PAGINA, inicio)
        if not pagina:
            return resultado
        for a in pagina:
            if a.ultima_visita is None or a.ultima_visita < desde:
                return resultado
            resultado.append(a)
        inicio += POR_PAGINA


def pagos_nuevos(pg: PowerGym, alumnos: list[Alumno], ultimo_id: int,
                 desde: datetime) -> list[tuple[Alumno, Movimiento]]:
    nuevos = []
    for a in alumnos:
        for m in pg.movimientos(a.id):
            if m.es_pago and m.id > ultimo_id and m.fecha >= desde:
                nuevos.append((a, m))
    nuevos.sort(key=lambda x: x[1].id)
    return nuevos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=None,
                    help="ignorar la última corrida y mirar N días hacia atrás")
    args = ap.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    pg = PowerGym(config["powergym_url"], config["powergym_cookie"])
    gf = None
    if config.get("gymflow_token"):
        gf = GymFlow(config.get("gymflow_url", "https://sistema.gymflow.com.ar"),
                     config["gymflow_token"])
    estado = leer_estado()

    ahora = datetime.now()
    if args.dias is not None or "ultima_corrida" not in estado:
        desde = ahora - timedelta(days=args.dias or 7)
        ultimo_id = 0
    else:
        desde = datetime.fromisoformat(estado["ultima_corrida"]) - MARGEN
        ultimo_id = estado.get("ultimo_movimiento_id", 0)

    alumnos = alumnos_a_revisar(pg, desde)
    print(f"Alumnos que vinieron desde {desde:%d/%m/%Y %H:%M}: {len(alumnos)}")
    nuevos = pagos_nuevos(pg, alumnos, ultimo_id, desde)

    with REPORTE.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["DNI", "Alumno", "Actividades", "Fecha pago", "Detalle",
                    "Forma de pago", "Monto", "Saldo actual", "ID movimiento",
                    "GymFlow: plan", "GymFlow: vence", "GymFlow: estado"])
        socios = {}
        for a, m in nuevos:
            gf_cols = ["", "", "sin revisar"]
            if gf and a.dni:
                if a.dni not in socios:
                    socios[a.dni] = gf.buscar_por_dni(a.dni)
                s = socios[a.dni]
                if s is None:
                    gf_cols = ["", "", "NO ESTÁ EN GYMFLOW"]
                else:
                    estado = "debe" if s.debe else (s.estado_pago or "")
                    gf_cols = [s.plan or "", f"{s.vence:%d/%m/%Y}" if s.vence else "", estado]
            w.writerow([a.dni or "SIN DNI", a.nombre, a.actividades,
                        f"{m.fecha:%d/%m/%Y}", m.detalle, m.forma_pago or "",
                        str(m.monto or "").replace(".", ","),
                        str(a.saldo or "").replace(".", ","), m.id, *gf_cols])

    print(f"Pagos nuevos: {len(nuevos)} -> {REPORTE.name}")

    estado["ultima_corrida"] = ahora.isoformat(timespec="seconds")
    if nuevos:
        estado["ultimo_movimiento_id"] = max(ultimo_id, nuevos[-1][1].id)
    ESTADO.write_text(json.dumps(estado, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
