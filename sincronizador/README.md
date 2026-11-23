# Sincronizador Power Gym → GymFlow

Mientras conviven los dos sistemas, este programa busca los **pagos nuevos** cargados
en Power Gym para pasarlos a GymFlow, cruzando a los alumnos por **DNI**.

Por cada pago nuevo busca al alumno por DNI en GymFlow y le carga la membresía con el
pago. Lo que no puede decidir solo (alumno que no está, plan sin equivalencia, alumno
que en GymFlow ya figura vigente, etc.) queda en un reporte para hacerlo a mano.

## Cómo funciona

1. Pide a Power Gym la lista de alumnos ordenada por **última visita**.
2. Revisa solo los que vinieron desde la corrida anterior (con 3 días de margen).
3. Abre la cuenta corriente de cada uno y toma los **pagos** (no los cargos de cuota)
   que todavía no se habían pasado.
4. Busca al alumno por DNI en GymFlow y decide:
   - si no está, si su plan o forma de pago no tiene equivalencia, o si en GymFlow ya
     está vigente → **a mano** (queda en el reporte con el motivo);
   - si no → carga una membresía desde la fecha del pago por los meses del plan, con
     el monto pagado.
5. Deja un reporte por corrida en `reportes/` (se abre con Excel) y guarda en
   `estado.json` hasta qué pago llegó, para no cargar nada dos veces.

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
  "gymflow_token": "PEGAR ACÁ EL VALOR DE gf_token",
  "cash_shift_id": 3296,
  "planes": {
    "MUSCULACION 2026": {"plan_id": 1751, "meses": 1}
  },
  "formas_pago": {
    "Efectivo": 843
  }
}
```

- `planes`: para cada texto de actividades de Power Gym (como aparece en la lista de
  alumnos), qué plan de GymFlow corresponde y cuántos meses dura.
- `formas_pago`: forma de pago de Power Gym → ID de medio de pago en GymFlow.
- `cash_shift_id`: turno de caja de GymFlow donde se registran los cobros.

Los IDs se ven con F12 al registrar un pago a mano en GymFlow (`plan_id`,
`cash_payment_method_id`, `cash_shift_id`).

Los valores de las cookies (`powergym_session` y `gf_token`) se sacan con F12 → Network → cualquier llamada → Cookie.
**Es como una contraseña: no compartir ni subir `config.json`.**

## Uso

```bash
python sincronizar.py            # MODO PRUEBA: solo muestra qué haría (no toca GymFlow)
python sincronizar.py --cargar   # carga de verdad
python sincronizar.py --dias 15 --cargar   # revisar un período más largo
```

Siempre conviene correr primero el modo prueba y mirar el reporte `_prueba.csv`.

## Tests

```bash
pip install pytest
python -m pytest tests
```
