# MQTT Logger Service

Servicio de logging para MQTT que se conecta a un broker Mosquitto, se suscribe al tópico `iot/+/status` y registra todos los mensajes recibidos.

## Características

- ✅ Conexión automática a broker Mosquitto
- ✅ Suscripción con wildcards (`iot/+/status`)
- ✅ Logging rotativo de mensajes
- ✅ Reconexión automática
- ✅ Configuración mediante archivo INI
- ✅ Servicio systemd para ejecución automática
- ✅ Graceful shutdown

## Requisitos

- Python 3.6+
- Mosquitto broker (local o remoto)
- Ubuntu/Debian Linux (para servicio systemd)

## Instalación

### 1. Instalar Mosquitto MQTT Broker

#### Instalación desde APT (recomendado)

```bash
# Actualizar repositorios
sudo apt update

# Instalar Mosquitto y clientes
sudo apt install mosquitto mosquitto-clients

# Verificar versión instalada
mosquitto -h | head -n 1
```

#### Configuración inicial

Editar la configuración de Mosquitto para permitir conexiones locales:

```bash
# Editar configuración principal
sudo nano /etc/mosquitto/mosquitto.conf
```

Asegurar que tenga al menos estas líneas:
```ini
listener 1883 localhost
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
include_dir /etc/mosquitto/conf.d
```

Para desarrollo, permitir conexiones anónimas:
```bash
# Editar configuración de autenticación
sudo nano /etc/mosquitto/conf.d/default.conf
```

Contenido:
```ini
allow_anonymous true
```

#### Iniciar y habilitar el servicio

```bash
# Iniciar servicio systemd
sudo systemctl start mosquitto

# Habilitar inicio automático
sudo systemctl enable mosquitto

# Verificar estado
sudo systemctl status mosquitto
```

#### Verificar funcionamiento

```bash
# En una terminal, suscribirse a un tópico de prueba
mosquitto_sub -h localhost -t "test/topic" -v

# En otra terminal, publicar un mensaje
mosquitto_pub -h localhost -t "test/topic" -m "¡Hola MQTT!"
```

Si ves el mensaje en la primera terminal, Mosquitto está funcionando correctamente.

#### Permitir conexiones externas

Por defecto, la configuración anterior permite solo conexiones locales. Para permitir que dispositivos externos se conecten al broker:

```bash
# Editar configuración
sudo nano /etc/mosquitto/mosquitto.conf
```

Cambiar la línea `listener 1883 localhost` por:
```ini
listener 1883
```

Esto hará que Mosquitto escuche en todas las interfaces de red.

```bash
# Reiniciar Mosquitto para aplicar cambios
sudo systemctl restart mosquitto

# Verificar que está escuchando en todas las interfaces
sudo ss -tlnp | grep 1883
```

**Salida esperada:**
```
LISTEN 0.0.0.0:1883  (escuchando en todas las interfaces IPv4)
LISTEN [::]:1883     (escuchando en todas las interfaces IPv6)
```

**Obtener la IP del servidor:**
```bash
hostname -I
```

Ahora los dispositivos externos pueden conectarse usando la IP del servidor (ejemplo: `10.0.2.15:1883`).

> **Nota de seguridad**: Si el servidor está expuesto a internet, considera configurar autenticación con `mosquitto_passwd` y usar certificados SSL/TLS.

#### Configuración para VirtualBox (si aplica)

Si estás ejecutando Ubuntu en una máquina virtual de VirtualBox, la IP `10.0.2.x` es una red NAT interna. Para permitir conexiones desde otros dispositivos en tu red local:

**1. Cambiar a Adaptador Puente (puede ser en caliente, sin apagar la VM):**

Desde VirtualBox en Windows:
1. Selecciona la VM (puede estar encendida)
2. Click en **Configuración** → **Red**
3. En **Adaptador 1**:
   - Conectado a: **Adaptador puente**
   - Nombre: Selecciona tu adaptador de red (WiFi o Ethernet)
4. Click **Aceptar**

La VM obtendrá automáticamente una nueva IP en la red local.

**2. Verificar la nueva IP desde Ubuntu:**

```bash
hostname -I
```

Deberías ver una IP como `192.168.1.35` (además de la de Docker `172.17.0.1`).

**3. Actualizar configuración de Mosquitto (opcional):**

Si quieres que Mosquitto escuche específicamente en la nueva IP:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Cambia `listener 1883` por `listener 1883 192.168.1.35` (usa tu IP actual).

```bash
sudo systemctl restart mosquitto
```

#### Habilitar acceso desde internet (Port Forwarding en router)

Para permitir conexiones desde internet a tu broker MQTT:

**1. Acceder al router:**
- Abre navegador y ve a: `http://192.168.1.1` o `http://192.168.0.1`
- Ingresa credenciales del router (usuario/contraseña)

**2. Buscar configuración de Port Forwarding:**

La ubicación varía según el router, busca alguna de estas opciones:
- **Reenvío de puertos**
- **Port Forwarding**
- **Servidor Virtual**
- **NAT / Virtual Server**
- **Aplicaciones y Juegos**

**3. Crear regla de reenvío:**

Configura una nueva regla con estos valores:

| Campo | Valor |
|-------|-------|
| Nombre/Descripción | MQTT Broker |
| Puerto Externo | 1883 |
| Puerto Interno | 1883 |
| IP Interna | 192.168.1.35 (tu IP de Ubuntu) |
| Protocolo | TCP |

**4. Guardar y aplicar cambios**

**5. Obtener tu IP pública:**

Desde Ubuntu:
```bash
curl ifconfig.me
```

O desde cualquier navegador: [https://www.whatismyip.com](https://www.whatismyip.com)

**6. Probar conexión externa:**

Desde un dispositivo fuera de tu red (usando datos móviles, por ejemplo):

```bash
mosquitto_pub -h TU_IP_PUBLICA -t "iot/test/status" -m "Mensaje desde internet"
```

> **⚠️ Importante**: 
> - La IP pública puede cambiar si tu proveedor usa IP dinámica
> - Considera usar un servicio DDNS (Dynamic DNS) para un dominio estable
> - En producción, **siempre** configura autenticación y SSL/TLS

### 2. Instalar dependencias de Python

```bash
# Instalar Python y pip si no están instalados
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Crear entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Instalar dependencias de Python
pip install -r requirements.txt
```

> **Nota**: Para desactivar el entorno virtual, ejecuta `deactivate`

### 3. Configurar el servicio

Edita el archivo `config.ini` según tus necesidades:

```ini
[MQTT]
broker = localhost        # Dirección del broker
port = 1883              # Puerto del broker
topic = iot/+/status     # Tópico a suscribirse
username =               # Usuario (opcional)
password =               # Contraseña (opcional)

[LOGGING]
log_dir = /var/log/mqtt-logger
log_file = mqtt-messages.log
log_level = INFO
```

### 4. Crear directorio de logs

```bash
# Crear directorio de logs con permisos para tu usuario
sudo mkdir -p /var/log/mqtt-logger
sudo chown $USER:$USER /var/log/mqtt-logger
```

### 5. Instalar y activar el servicio systemd

#### Instalación

```bash
# Copiar el archivo de servicio a systemd
sudo cp mqtt-logger.service /etc/systemd/system/

# Recargar configuración de systemd
sudo systemctl daemon-reload

# Habilitar el servicio para inicio automático al arrancar
sudo systemctl enable mqtt-logger.service

# Iniciar el servicio
sudo systemctl start mqtt-logger.service
```

#### Verificar estado del servicio

```bash
# Ver estado completo del servicio
sudo systemctl status mqtt-logger
```

**Salida esperada:**
```
● mqtt-logger.service - MQTT Logger Service
     Loaded: loaded (/etc/systemd/system/mqtt-logger.service; enabled)
     Active: active (running) since Fri 2025-11-21 13:50:21 -03
   Main PID: 19482 (python)
```

Si ves `Active: active (running)` en verde, el servicio está funcionando correctamente.

#### Monitorear logs del servicio

```bash
# Ver logs del servicio systemd (últimas 20 líneas)
sudo journalctl -u mqtt-logger -n 20

# Ver logs en tiempo real (seguir nuevos mensajes)
sudo journalctl -u mqtt-logger -f

# Ver logs desde hoy
sudo journalctl -u mqtt-logger --since today
```

#### Verificar logs de mensajes MQTT

```bash
# Ver últimas 20 líneas del log de mensajes
tail -n 20 /var/log/mqtt-logger/mqtt-messages.log

# Ver logs en tiempo real (seguir nuevos datos)
tail -f /var/log/mqtt-logger/mqtt-messages.log

# Buscar mensajes de un sensor específico
grep "iot/sensor1/status" /var/log/mqtt-logger/mqtt-messages.log

# Contar cuántos mensajes se han recibido
grep "Topic:" /var/log/mqtt-logger/mqtt-messages.log | wc -l
```

#### Gestión del servicio

## Uso del Servicio

El servicio se ejecuta automáticamente en segundo plano. No necesitas ejecutarlo manualmente.

### Comandos de gestión

```bash
# Detener el servicio
sudo systemctl stop mqtt-logger

# Reiniciar el servicio (útil después de modificar script.py o config.ini)
sudo systemctl restart mqtt-logger

# Ver estado en tiempo real
sudo systemctl status mqtt-logger
```

> **Nota**: Si modificas `script.py` o `config.ini`, reinicia el servicio para aplicar los cambios.

## Pruebas

### Publicar mensajes de prueba

El script se suscribe al tópico `iot/+/status` donde `+` es un wildcard de un nivel. Publica mensajes de prueba usando `mosquitto_pub`:

```bash
# Mensaje simple de temperatura
mosquitto_pub -h localhost -t "iot/sensor1/status" -m "Temperature: 25°C"

# Mensaje de humedad
mosquitto_pub -h localhost -t "iot/sensor2/status" -m "Humidity: 60%"

# Mensaje JSON
mosquitto_pub -h localhost -t "iot/device3/status" -m '{"temp":23,"humidity":55,"battery":85}'

# Mensaje de estado
mosquitto_pub -h localhost -t "iot/gateway/status" -m "online"
```

### Verificar que se registran los mensajes

```bash
# Ver logs en tiempo real
sudo tail -f /var/log/mqtt-logger/mqtt-messages.log

# O si ejecutas manualmente (con venv activado)
tail -f /var/log/mqtt-logger/mqtt-messages.log
```

**Ejemplo de salida esperada:**
```
2025-11-21 13:45:30 - root - INFO - Topic: iot/sensor1/status | QoS: 0 | Message: Temperature: 25°C
2025-11-21 13:45:35 - root - INFO - Topic: iot/sensor2/status | QoS: 0 | Message: Humidity: 60%
2025-11-21 13:45:40 - root - INFO - Topic: iot/device3/status | QoS: 0 | Message: {"temp":23,"humidity":55,"battery":85}
```

## Estructura de archivos

```
mqtt-to-mysql/
├── script.py              # Script principal del cliente MQTT
├── config.ini            # Archivo de configuración
├── requirements.txt      # Dependencias de Python
├── mqtt-logger.service   # Archivo de servicio systemd
└── README.md            # Este archivo
```

## Formato de logs

Los logs se guardan en el formato:

```
YYYY-MM-DD HH:MM:SS - root - INFO - Topic: iot/sensor1/status | QoS: 0 | Message: Temperature: 25°C
```

## Troubleshooting

### El servicio no inicia

```bash
# Ver logs detallados
sudo journalctl -u mqtt-logger -n 50 --no-pager

# Verificar permisos
ls -la /var/log/mqtt-logger

# Verificar que el broker está corriendo
sudo systemctl status mosquitto
```

### No se reciben mensajes

1. Verifica que el broker está corriendo: `sudo systemctl status mosquitto`
2. Verifica la configuración del tópico en `config.ini`
3. Prueba la conexión manualmente ejecutando `python3 script.py`

### Problemas de permisos

```bash
# Dar permisos al usuario mqtt-logger
sudo chown -R mqtt-logger:mqtt-logger /var/log/mqtt-logger
sudo chmod 755 /var/log/mqtt-logger
```

## Licencia

MIT