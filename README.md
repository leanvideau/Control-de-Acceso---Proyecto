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
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw allow in on tailscale0
```
Y además agregamos un programa, que sirve para que los comandos que demoran, tengan un respaldo de que si se cae la conexión SSH, los mismos sigan corriendo. Programa: **tmux**

<img width="1118" height="583" alt="Captura de pantalla 2026-11-03 171640" src="https://github.com/user-attachments/assets/d0f2f248-5733-4670-82cb-f9348f9acb9b" />

## Configuración de sistema

Para la configuración principal del sistema vamos a agregar un usuario aparte al técnico del sistema y le otorgamos los privilegios necesarios dentro del dispositivo. La conexión se hará por SSH mediante Tailscale (VPN privada para establecer una conexión SSH segura) ya que no conviene abrir el puerto 22 al router sabiendo que hay muchos bots haciendo ataques de fuerza bruta constantemente en la red, entonces es un riesgo completamente evitable. <br>

Luego de que el técnico haya instalado todo lo necesario en la PC principal y en la Raspberry (Access Bridge), configuramos nuevamente el firewall para que permita conexiones en el puerto 7777 que sería donde se encuentra el Websocket.<br>
```bash
sudo ufw allow from 192.168.1.0/24 to any port 7777 proto tcp
```
Luego procedemos a probar si el Access Bridge le transmite la conexión al Raspberry, cuando vimos que todo funcionaba solo quedaba, configurar el sistema y conectar el relé y la cerradura magnética. 
En el sistema le asignamos a cada profesor el rol de personal, para que puedan entrar con su DNI sin ningún problema, y la concedemos a cada uno una cuenta con una contraseña para que tengan sus datos, sus rutinas, la alimentación de sus alumnos, y demás a su disposición.<br>
Además importamos los datos de los alumnos al nuevo sistema con su membresía correspondiente.

Para la actualización constante de las membresías de los alumnos hice un programa de python con Claude Opus 5.5 que mediante las cookies de sesión se conecte con las 2 plataformas, Power Gym y Gym Flow, revise los últimos alumnos que pagaron en los 2 sistemas y que haga los cambios necesarios automáticamente, siempre y cuando si le soy permiso para hacerlo. <br>
## Conexión del hardware

Con el sistema funcionando, pasamos a la parte física. Primero conectamos el relé a la Raspberry: el relé tiene tres bornes de control (DC+, DC− e IN) que van a los pines GPIO de la Pi, y el jumper del relé lo dejamos en **H** (High Level Trigger) para que se active cuando la Pi le manda señal alta.<br>

| Pin Raspberry | Función | Borne del relé |
|---|---|---|
| Pin 2 | 5V | DC+ |
| Pin 9 | GND | DC− |
| Pin 11 | GPIO17 (señal) | IN |

El pin 2 le da energía al relé, el pin 9 es la tierra común entre los dos y el pin 11 es la señal con la que la Pi le indica al relé cuándo activarse. De esta forma la Raspberry nunca está en contacto con los 12V de la cerradura: el relé funciona como intermediario entre los dos circuitos.<br>

<img width="1600" height="1200" alt="WhatsApp Image 2026-11-26 at 12 15 46 AM" src="https://github.com/user-attachments/assets/1e702cdc-300f-4b8b-b9f5-17f1e1c84329" />


Para comprobar que la Pi controla el relé, ejecutamos una prueba que lo activa durante 2 segundos:
```bash
python3 -c "from gpiozero import OutputDevice; from time import sleep; r = OutputDevice(17, active_high=True, initial_value=False); r.on(); sleep(2); r.off()"
```
<!-- video o foto del relé activado -->

### Relé → Cerradura magnética
<!-- se completa al instalar la cerradura: fuente 12V → COM, NC → botón de salida → cerradura -->
<img width="2200" height="1480" alt="imagen" src="https://github.com/user-attachments/assets/c44d581d-f861-49ee-bf95-93a3e478082b" />
