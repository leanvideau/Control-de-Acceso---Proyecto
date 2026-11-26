"""Baja la última versión del programa desde GitHub y reemplaza los archivos.

Nunca toca config.json, estado.json ni la carpeta reportes/.
Si no hay internet o falla, sigue con la versión que ya está.
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = "https://github.com/leanvideau/Control-de-Acceso---Proyecto/archive/refs/heads/"
RAMAS = ["main", "claude/project-thread-hhdgst"]  # primero la principal, si ya se mergeó
CARPETA = Path(__file__).parent
NO_TOCAR = {"config.json", "estado.json"}


def bajar_zip() -> zipfile.ZipFile | None:
    for rama in RAMAS:
        try:
            with urllib.request.urlopen(REPO + rama + ".zip", timeout=30) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
            if any("/sincronizador/sincronizar.py" in n for n in z.namelist()):
                return z
        except Exception:
            continue
    return None


def actualizar(z: zipfile.ZipFile, destino: Path) -> list[str]:
    cambiados = []
    for nombre in z.namelist():
        if "/sincronizador/" not in nombre or nombre.endswith("/"):
            continue
        relativo = nombre.split("/sincronizador/", 1)[1]
        if relativo in NO_TOCAR or relativo.startswith("reportes/"):
            continue
        nuevo = z.read(nombre)
        archivo = destino / relativo
        if archivo.exists() and archivo.read_bytes() == nuevo:
            continue
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(nuevo)
        cambiados.append(relativo)
    return cambiados


def main() -> None:
    print("Buscando actualizaciones...")
    z = bajar_zip()
    if z is None:
        print("No se pudo bajar la última versión. Sigo con la que está.")
        return
    cambiados = actualizar(z, CARPETA)
    print(f"Actualizado: {', '.join(cambiados)}" if cambiados else "Ya tenés la última versión.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # nunca frenar la sincronización por esto
        print(f"No se pudo actualizar ({e}). Sigo con la versión que está.", file=sys.stderr)
