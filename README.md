# Control-de-Acceso---Proyecto
Documentación del proceso de implementación del sistema de acceso.
El gimnasio que administro necesita un cambio de acceso ya que hay alumnos que directamente no pagan la mensualidad.

## Investigación

Primero que nada investigué miles de sistemas de gimnasios habían muchos que eran muy complejos, hasta que encontré uno perfecto y mas que nada lo elegí para aprender justo un tema de la carrera que estudio. El sistema se llama GYM Flow y trabaja con molinetes principalmente pero consultando al soporte me dijieron que podía configurar un microcontrolador Raspberry Pi 3 conectado con un Relé de 5V 10A estos componentes funcionan juntos de la siguiente forma:
    
    El Raspberry Pi 3 conectado con la PC Windows recibe una señal de que un cliente introdujo su DNI y que ha pagado el mismo dispositivo luego le "dice" al Relé que se apague para que la cerradura magnética se abra automaticamente. 
