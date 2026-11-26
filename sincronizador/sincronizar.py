"""Busca los pagos nuevos en Power Gym desde la última corrida.

Por cada pago busca al alumno por DNI en GymFlow y, si está todo claro, le carga
la membresía con el pago. Lo que no se puede decidir solo queda en el reporte
(carpeta reportes/) para hacerlo a mano.

Uso:
    python sincronizar.py                    # MODO PRUEBA: solo muestra qué haría
    python sincronizar.py --cargar           # carga en GymFlow, preguntando uno por uno
    python sincronizar.py --dias 10          # mirar los últimos 10 días

Configuración en config.json (NO subirlo a ningún lado, tiene la sesión):
    {"powergym_url": "https://laroca.sistemapowergym.com",
     "powergym_cookie": "valor de powergym_session",
     "gymflow_url": "https://sistema.gymflow.com.ar",
     "gymflow_token": "valor de gf_token",
     "planes": [{"powergym": ["MUSCULACION 2026"], "plan_id": 1751, "dias": 30}],
     "formas_pago": {"Efectivo": 843}}
    (ver config.ejemplo.json con la tabla completa)
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

from gymflow import GymFlow
from membresias import decidir, planes_gymflow
from powergym import Alumno, Movimiento, PowerGym

CARPETA = Path(__file__).parent
CONFIG = CARPETA / "config.json"
ESTADO = CARPETA / "estado.json"
REPORTES = CARPETA / "reportes"   # un CSV por corrida, para no perder nada

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


def confirmar(a: Alumno, m: Movimiento, motivo: str) -> bool:
    """Pregunta antes de tocar GymFlow. Lean quiere aprobar cada cambio."""
    print()
    print(f"  {a.nombre} (DNI {a.dni}) pagó {m.forma_pago} $ {m.monto} el {m.fecha:%d/%m/%Y} ({m.detalle})")
    print(f"  -> {motivo}")
    while True:
        r = input("  ¿Lo cargo en GymFlow? [s/n]: ").strip().lower()
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False


def elegir_plan(a: Alumno, m: Movimiento, planes: list[dict]) -> dict | None:
    """Para alumnos sin actividad (o con una sin equivalencia): Lean elige el plan."""
    print()
    print(f"  {a.nombre} (DNI {a.dni}) pagó {m.forma_pago} $ {m.monto} el {m.fecha:%d/%m/%Y} ({m.detalle})")
    print(f"  En Power Gym figura: {a.actividades or 'sin actividades'}")
    print("  ¿Con qué plan lo cargo en GymFlow?")
    for i, p in enumerate(planes, 1):
        print(f"    {i}. {p.get('nombre', p['plan_id'])} ({p.get('dias', 30)} días)")
    print("    0. No cargarlo (lo hago a mano)")
    while True:
        r = input("  Número: ").strip()
        if r.isdigit() and 0 <= int(r) <= len(planes):
            return planes[int(r) - 1] if int(r) else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=None,
                    help="ignorar la última corrida y mirar N días hacia atrás")
    ap.add_argument("--cargar", action="store_true",
                    help="cargar en GymFlow preguntando antes cada uno (sin esto solo muestra qué haría)")
    args = ap.parse_args()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    pg = PowerGym(config["powergym_url"], config["powergym_cookie"])
    gf = GymFlow(config.get("gymflow_url", "https://sistema.gymflow.com.ar"),
                 config["gymflow_token"])
    estado = leer_estado()
    cargados = set(estado.get("cargados", []))

    ahora = datetime.now()
    if args.dias is not None or "ultima_corrida" not in estado:
        desde = ahora - timedelta(days=args.dias or 7)
        ultimo_id = 0
    else:
        desde = datetime.fromisoformat(estado["ultima_corrida"]) - MARGEN
        ultimo_id = estado.get("ultimo_movimiento_id", 0)

    alumnos = alumnos_a_revisar(pg, desde)
    print(f"Alumnos que vinieron desde {desde:%d/%m/%Y %H:%M}: {len(alumnos)}")
    nuevos = [(a, m) for a, m in pagos_nuevos(pg, alumnos, ultimo_id, desde)
              if m.id not in cargados]
    print("MODO REAL: se carga en GymFlow" if args.cargar else
          "MODO PRUEBA: no se toca GymFlow (usar --cargar para cargar)")

    REPORTES.mkdir(exist_ok=True)
    reporte = REPORTES / f"pagos_{ahora:%Y-%m-%d_%H%M}{'' if args.cargar else '_prueba'}.csv"
    socios: dict = {}
    n_cargados = n_manual = 0
    with reporte.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["DNI", "Alumno", "Actividades", "Fecha pago", "Detalle",
                    "Forma de pago", "Monto", "Saldo actual", "ID movimiento",
                    "GymFlow: plan", "GymFlow: vence", "GymFlow: estado", "Acción"])
        for a, m in nuevos:
            socio = None
            if a.dni:
                if a.dni not in socios:
                    socios[a.dni] = gf.buscar_por_dni(a.dni)
                socio = socios[a.dni]
            gf_cols = ["", "", "NO ESTÁ EN GYMFLOW"]
            if socio:
                estado_gf = "debe" if socio.debe else (socio.estado_pago or "")
                gf_cols = [socio.plan or "",
                           f"{socio.vence:%d/%m/%Y}" if socio.vence else "", estado_gf]

            decision = decidir(a, m, socio, config)
            if decision.falta_plan and args.cargar:
                plan = elegir_plan(a, m, planes_gymflow(config))
                if plan:
                    decision = decidir(a, m, socio, config, plan=plan)
                else:
                    decision.motivo = "NO cargado (elegiste no cargarlo): " + decision.motivo
            accion = decision.motivo
            if decision.datos is None:
                n_manual += 1
                if decision.falta_plan and not args.cargar:
                    accion = "Te va a preguntar el plan. " + accion
            elif args.cargar and not confirmar(a, m, decision.motivo):
                accion = "NO cargado (dijiste que no): " + accion
                n_manual += 1
            elif args.cargar:
                try:
                    gf.crear_membresia(decision.datos)
                    cargados.add(m.id)
                    n_cargados += 1
                    accion = "CARGADO: " + accion
                    socios.pop(a.dni, None)  # que la próxima búsqueda vea la membresía nueva
                except Exception as e:  # seguimos con los demás y queda en el reporte
                    accion = f"ERROR al cargar: {e}"
                    n_manual += 1
            else:
                accion = "Se cargaría: " + accion

            w.writerow([a.dni or "SIN DNI", a.nombre, a.actividades,
                        f"{m.fecha:%d/%m/%Y}", m.detalle, m.forma_pago or "",
                        str(m.monto or "").replace(".", ","),
                        str(a.saldo or "").replace(".", ","), m.id, *gf_cols, accion])

    print(f"Pagos nuevos: {len(nuevos)} | cargados: {n_cargados} | "
          f"para hacer a mano: {n_manual} -> {reporte}")

    # En modo prueba no avanzamos el marcador, así la corrida real ve los mismos pagos.
    if args.cargar:
        estado["ultima_corrida"] = ahora.isoformat(timespec="seconds")
        if nuevos:
            estado["ultimo_movimiento_id"] = max(ultimo_id, max(m.id for _, m in nuevos))
        estado["cargados"] = sorted(cargados)[-500:]
        ESTADO.write_text(json.dumps(estado, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
