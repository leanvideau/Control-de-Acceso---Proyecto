# Control-de-Acceso---Proyecto
Documentación del proceso de implementación del sistema de acceso.
El gimnasio del que estoy encargado necesita un cambio de control de acceso, para mantener controlado a cada alumno

## Investigación

Primero investigué muchos sistemas de gimnasios, encontré uno que encajaba perfectamente con lo que necesitaba. El sistema se llama GYM Flow y trabaja con molinetes principalmente, pero consultando al soporte, me dijeron que podía configurar un microcontrolador Raspberry Pi 3 conectado con un Relé de 5V 10A estos componentes funcionan juntos de la siguiente forma:        
    El Raspberry Pi 3 conectado con la PC Windows recibe una señal de que un cliente introdujo su DNI y que ha pagado, el mismo dispositivo luego le "dice" al Relé que se apague para que la cerradura magnética se abra automáticamente. 

## Configuración Inicial

Luego de comprar todas las cosas necesarias (Fuente, Micro SD, Gabinete, etc), instalamos el Sistema Operativo Raspberry PI OS en la Micro SD para que mas adelante nos podamos establecer una conexión con el Raspberry mediante SSH.

<img width="1111" height="333" alt="imagen" src="https://github.com/user-attachments/assets/dd77e1e1-8382-4a5c-a412-710caa2d0740" />

Luego de conectarnos actualizamos las credenciales, agregamos acceso por llaves SSH y actualizamos el sistema operativo para tener todo funcionando perfectamente.<br>
Ahora necesitamos agregarle la seguridad correspondiente al dispositivo, ya que es un activo crítico. Primero instalamos un programa que se encarga de actualizar automáticamente para tener todos los parches de seguridad al día. Programa: **unattended-upgrades**.<br>
Agregamos un Firewall (explicación de la config). <br>
Y además agregamos un programa que sirve para que comandos que demoran tenga un respaldo de que si se cae la conexión se reanuda el proceso. Programa: **tmux**

<img width="1118" height="583" alt="Captura de pantalla 2026-11-03 171640" src="https://github.com/user-attachments/assets/d0f2f248-5733-4670-82cb-f9348f9acb9b" />
