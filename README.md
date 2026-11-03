# Control-de-Acceso---Proyecto
Documentación del proceso de implementación del sistema de acceso.
El gimnasio que administro necesita un cambio de acceso ya que hay alumnos que directamente no pagan la mensualidad.

## Investigación

Primero que nada investigué miles de sistemas de gimnasios habían muchos que eran muy complejos, hasta que encontré uno perfecto y mas que nada lo elegí para aprender justo un tema de la carrera que estudio. El sistema se llama GYM Flow y trabaja con molinetes principalmente pero consultando al soporte me dijeron que podía configurar un microcontrolador Raspberry Pi 3 conectado con un Relé de 5V 10A estos componentes funcionan juntos de la siguiente forma:        
    El Raspberry Pi 3 conectado con la PC Windows recibe una señal de que un cliente introdujo su DNI y que ha pagado el mismo dispositivo luego le "dice" al Relé que se apague para que la cerradura magnética se abra automáticamente. 

## Configuración Inicial

Luego de comprar todas las cosas necesarias (Fuente, Micro SD, Gabinete, etc), instalamos el Sistema Operativo Raspberry PI OS en la Micro SD para que mas adelante nos podamos establecer una conexión con el Raspberry mediante SSH.

<img width="1111" height="333" alt="imagen" src="https://github.com/user-attachments/assets/dd77e1e1-8382-4a5c-a412-710caa2d0740" />

Luego de conectarnos actualizamos las credenciales, agregamos acceso por llaves SSH y actualizamos el sistema operativo para tener todo funcionando perfectamente
