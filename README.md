# Control-de-Acceso---Proyecto
Documentación del proceso de implementación del sistema de acceso.
El gimnasio del que estoy encargado necesita un cambio de control de acceso, para mantener controlado a cada alumno.

## Investigación

Primero investigué muchos sistemas de gimnasios, encontré uno que encajaba perfectamente con lo que necesitaba. El sistema se llama GymFlow y trabaja con molinetes principalmente, pero consultando al soporte, me dijeron que podía configurar un Raspberry Pi 3 conectado con un Relé de 5V 10A. Estos componentes funcionan juntos de la siguiente forma:        
   la PC con Windows corre el Access Bridge, que valida contra GymFlow. Si el DNI está al día, le avisa por WebSocket a un servicio en Python en la Pi, y la Pi activa el relé, que corta la alimentación de la cerradura y la puerta se libera.

## Configuración Inicial

Luego de comprar todas las cosas necesarias (Fuente, Micro SD, Gabinete, etc), instalamos el Sistema Operativo Raspberry Pi OS (Debian 13) en la Micro SD desactivando Raspberry Pi Connect,que permite entrar a la Pi de cualquier lugar del mundo y esto no conviene ya que es un riesgo, y es evitable <br>
Mas adelante logramos establecer una conexión con el Raspberry mediante SSH para configurar todo lo necesario.

<img width="1111" height="333" alt="imagen" src="https://github.com/user-attachments/assets/dd77e1e1-8382-4a5c-a412-710caa2d0740" />

Luego de conectarnos actualizamos las credenciales, agregamos acceso por llaves SSH y actualizamos el sistema operativo para tener todo funcionando perfectamente.<br>
Ahora necesitamos agregarle la seguridad correspondiente al dispositivo, ya que es un activo crítico. Primero instalamos un programa que se encarga de actualizar automáticamente para tener todos los parches de seguridad al día. Programa: **unattended-upgrades**.<br>
Agregamos un Firewall, aplicándole las reglas correspondientes, primero para empezar dejamos todo lo que entre a la red deshabilitado menos el puerto 22 dentro de la red y por Tailscale, y todo lo que sale lo dejamos habilitado. <br>
'''bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw allow in on tailscale0
'''
Y además agregamos un programa, que sirve para que los comandos que demoran, tengan un respaldo de que si se cae la conexión SSH, los mismos sigan corriendo. Programa: **tmux**

<img width="1118" height="583" alt="Captura de pantalla 2026-11-03 171640" src="https://github.com/user-attachments/assets/d0f2f248-5733-4670-82cb-f9348f9acb9b" />

## Configuración de sistema

Para la configuración principal del sistema vamos a agregar un usuario aparte al técnico del sistema y le otorgamos los privilegios necesarios dentro del dispositivo. La conexión se hará por SSH mediante Tailscale (VPN privada para establecer una conexión SSH segura) ya que no conviene abrir el puerto 22 al router sabiendo que hay muchos bots haciendo ataques de fuerza bruta constantemente en la red, entonces es un riesgo completamente evitable. <br>

