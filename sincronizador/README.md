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
5. Los alumnos que pagaron pero **no están en GymFlow** van además a un archivo aparte,
   `reportes/alumnos_para_agregar_<fecha>.csv`, con DNI, nombre, teléfono, plan
   sugerido, pago y vencimiento sugerido, para darlos de alta a mano.
6. Deja un reporte por corrida en `reportes/` (se abre con Excel) y guarda en
   `estado.json` hasta qué pago llegó, para no cargar nada dos veces.

Limitación: si un alumno paga y no viene al gym en esos días, no aparece. En ese caso
correr `python sincronizar.py --dias 15` para revisar un período más largo.

## Instalación (PC con Windows)

1. Instalar Python 3 desde python.org (marcar "Add Python to PATH").
2. En esta carpeta: `pip install -r requirements.txt`
3. Copiar `config.ejemplo.json` como `config.json` y pegar las dos cookies
   (`powergym_session` y `gf_token`, se sacan con F12 → Network → cualquier llamada → Cookie).
   **Son como una contraseña: no compartir ni subir `config.json`.**

En `config.json`:
- `planes`: qué plan de GymFlow corresponde a cada combinación de actividades de
  Power Gym (tal cual aparecen en la lista de alumnos; el orden y las tildes no importan).
  Si un alumno no tiene actividades (o tiene una combinación que no está en la tabla),
  el programa te pregunta con qué plan cargarlo, o si preferís no cargarlo.
- `formas_pago`: forma de pago de Power Gym → ID del medio de pago en GymFlow
  (`null` = todavía no lo sabemos, esos pagos quedan para hacer a mano).
- `cash_shift_id` (opcional): turno de caja de GymFlow. Si no usan turnos, no ponerlo.

## Uso

```bash
python sincronizar.py            # MODO PRUEBA: solo muestra qué haría (no toca GymFlow)
python sincronizar.py --cargar   # carga, preguntando "¿Lo cargo? [s/n]" en cada uno
python sincronizar.py --dias 15 --cargar   # revisar un período más largo
```

En Windows también se puede hacer doble clic en `sincronizar.bat`.

Siempre conviene correr primero el modo prueba y mirar el reporte `_prueba.csv`.

## Tests

```bash
pip install pytest
python -m pytest tests
```
