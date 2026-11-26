"""Arma el Excel del reporte: una hoja de resumen, los pagos y los alumnos para agregar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

# categoría -> (color de fondo, explicación para la hoja Resumen)
CATEGORIAS = {
    "CARGADO":     ("C6EFCE", "Se cargó en GymFlow."),
    "SE CARGA":    ("C6EFCE", "Al correr sincronizar.bat se va a cargar (te pide sí o no)."),
    "TE PREGUNTA": ("FFEB9C", "Al correr sincronizar.bat te va a preguntar el plan o la forma de pago."),
    "NADA":        ("DDEBF7", "No hay que hacer nada: en GymFlow ya está al día."),
    "A MANO":      ("FFC7CE", "Lo tenés que hacer vos en GymFlow (dice por qué)."),
    "NO CARGADO":  ("EDEDED", "Elegiste no cargarlo."),
    "NO ES CUOTA": ("EDEDED", "Monto chico (agua, bebidas, etc.): no es una cuota, no se carga."),
    "ERROR":       ("FFC7CE", "Falló al cargar: revisalo a mano."),
}


@dataclass
class Fila:
    categoria: str
    que_pasa: str
    alumno: str
    dni: str
    fecha: datetime
    monto: Decimal | None
    forma_pago: str
    actividad: str
    en_gymflow: str
    detalle: str


def _ancho(ws, anchos):
    for col, ancho in zip("ABCDEFGHIJ", anchos):
        ws.column_dimensions[col].width = ancho


def _encabezado(ws, fila, titulos):
    for i, t in enumerate(titulos, 1):
        c = ws.cell(row=fila, column=i, value=t)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="404040")
        c.alignment = Alignment(wrap_text=True, vertical="center")


def escribir(ruta: Path, filas: list[Fila], para_agregar: list[list], modo_prueba: bool) -> None:
    wb = Workbook()

    # --- Resumen
    ws = wb.active
    ws.title = "Resumen"
    ws["A1"] = "Reporte de pagos Power Gym → GymFlow"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = (f"{datetime.now():%d/%m/%Y %H:%M} · "
                + ("MODO PRUEBA: no se cargó nada" if modo_prueba else "Corrida real"))
    _encabezado(ws, 4, ["Qué pasa", "Cantidad", "Qué significa"])
    r = 5
    for cat, (color, texto) in CATEGORIAS.items():
        n = sum(1 for f in filas if f.categoria == cat)
        if not n:
            continue
        ws.cell(row=r, column=1, value=cat).fill = PatternFill("solid", fgColor=color)
        ws.cell(row=r, column=2, value=n)
        ws.cell(row=r, column=3, value=texto)
        r += 1
    if r == 5:
        ws.cell(row=r, column=1, value="No hubo pagos nuevos.")
        r += 1
    ws.cell(row=r + 1, column=1, value="El detalle de cada pago está en la hoja 'Pagos'.")
    if para_agregar:
        ws.cell(row=r + 2, column=1,
                value=f"{len(para_agregar)} alumno(s) no existen en GymFlow: ver hoja 'Alumnos para agregar'.")
    _ancho(ws, [16, 10, 70])

    # --- Pagos
    ws = wb.create_sheet("Pagos")
    _encabezado(ws, 1, ["Qué pasa", "Alumno", "DNI", "Fecha del pago", "Monto",
                        "Forma de pago", "Actividad en Power Gym", "Cómo está en GymFlow",
                        "Detalle del pago"])
    for i, f in enumerate(filas, 2):
        valores = [f.que_pasa, f.alumno, f.dni, f.fecha.date(),
                   float(f.monto) if f.monto is not None else None, f.forma_pago,
                   f.actividad, f.en_gymflow, f.detalle]
        color = PatternFill("solid", fgColor=CATEGORIAS.get(f.categoria, ("FFFFFF",))[0])
        for j, v in enumerate(valores, 1):
            c = ws.cell(row=i, column=j, value=v)
            c.fill = color
            c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row=i, column=4).number_format = "DD/MM/YYYY"
        ws.cell(row=i, column=5).number_format = '"$" #,##0.00'
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{max(len(filas) + 1, 1)}"
    _ancho(ws, [55, 26, 12, 13, 12, 14, 30, 30, 24])

    # --- Alumnos para agregar
    if para_agregar:
        ws = wb.create_sheet("Alumnos para agregar")
        _encabezado(ws, 1, ["DNI", "Nombre", "Teléfono", "Actividad en Power Gym",
                            "Plan para GymFlow", "Fecha del pago", "Monto", "Forma de pago",
                            "Vence", "Detalle del pago"])
        for i, fila in enumerate(para_agregar, 2):
            for j, v in enumerate(fila, 1):
                ws.cell(row=i, column=j, value=v)
            ws.cell(row=i, column=6).number_format = "DD/MM/YYYY"
            ws.cell(row=i, column=7).number_format = '"$" #,##0.00'
            ws.cell(row=i, column=9).number_format = "DD/MM/YYYY"
        ws.freeze_panes = "A2"
        _ancho(ws, [12, 26, 14, 30, 24, 13, 12, 14, 12, 24])

    wb.save(ruta)
