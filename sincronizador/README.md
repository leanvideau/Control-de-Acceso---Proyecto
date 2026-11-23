# Sincronizador Power Gym → GymFlow

Mientras conviven los dos sistemas, este programa busca los **pagos nuevos** cargados
en Power Gym para pasarlos a GymFlow, cruzando a los alumnos por **DNI**.

Estado actual: lee Power Gym y arma `pagos_nuevos.csv` (se abre con Excel), con una
columna que muestra cómo está cada alumno en GymFlow (plan, vencimiento, si debe).
La carga automática en GymFlow se agrega cuando tengamos capturadas sus llamadas.

## Cómo funciona

1. Pide a Power Gym la lista de alumnos ordenada por **última visita**.
2. Revisa solo los que vinieron desde la corrida anterior (con 3 días de margen).
3. Abre la cuenta corriente de cada uno y toma los **pagos** (no los cargos de cuota)
   que todavía no se habían pasado.
4. Guarda en `estado.json` hasta qué pago llegó, para no repetir en la próxima corrida.

Limitación: si un alumno paga y no viene al gym en esos días, no aparece. En ese caso
correr `python sincronizar.py --dias 15` para revisar un período más largo.

## Instalación (PC con Windows)

1. Instalar Python 3 desde python.org (marcar "Add Python to PATH").
2. En esta carpeta: `pip install -r requirements.txt`
3. Crear `config.json`:

```json
{
  "powergym_url": "https://laroca.sistemapowergym.com",
  "powergym_cookie": "PEGAR ACÁ EL VALOR DE powergym_session",
  "gymflow_url": "https://sistema.gymflow.com.ar",
  "gymflow_token": "PEGAR ACÁ EL VALOR DE gf_token"
}
```

Los valores de las cookies (`powergym_session` y `gf_token`) se sacan con F12 → Network → cualquier llamada → Cookie.
**Es como una contraseña: no compartir ni subir `config.json`.**

## Uso

```bash
python sincronizar.py --dias 7   # primera vez
python sincronizar.py            # las siguientes
```

## Tests

```bash
pip install pytest
python -m pytest tests
```
