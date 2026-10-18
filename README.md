# Divoom Times Frame para Home Assistant

Integración personalizada para controlar localmente la pantalla Divoom Times Frame desde Home Assistant. La primera versión crea una entidad `light` para encender/apagar la pantalla y ajustar su brillo.

## Instalación

1. En HACS, abre **Integraciones** y selecciona **Repositorios personalizados**.
2. Añade `https://github.com/roldan931/hacs_divoom_times_frame` con la categoría **Integración**.
3. Descarga **Divoom Times Frame** y reinicia Home Assistant.
4. Ve a **Ajustes → Dispositivos y servicios → Añadir integración** y selecciona **Divoom Times Frame**.

## Configuración

El flujo de alta solicita:

- **IP** del Times Frame.
- **DeviceID** numérico del dispositivo en Divoom.
- **Puerto**, opcional, con `9000` como valor predeterminado.

La integración consulta `Channel/GetClockInfo` en la IP indicada y solo acepta el alta si la respuesta incluye el mismo `DeviceId` que se configuró. También repite la comprobación antes de leer estado y ejecutar comandos. Si el dispositivo no responde, no devuelve su ID o hay una discrepancia, la operación se rechaza. No se solicita la cuenta ni la contraseña de Divoom.

El DeviceID configurado se usa como identificador persistente del dispositivo dentro de Home Assistant. Aunque también se utiliza en el ecosistema cloud de Divoom, esta versión solo usa la API local; añadir características que consulten o modifiquen la nube podría requerir autenticación y permisos adicionales.

## Funciones actuales

- Entidad `light` para encendido/apagado.
- Brillo de Home Assistant (0–255) convertido al rango del dispositivo (0–100).
- Actualización del estado cada 30 segundos.
- Comunicación HTTP local con `GET` y cuerpo JSON a `/divoom_api`.

## Red y seguridad

El Times Frame debe estar accesible desde Home Assistant en la red local. La API observada usa HTTP sin autenticación en el puerto `9000`; el DeviceID se comprueba para evitar configurar por error otra pantalla, pero no es una credencial ni una prueba criptográfica contra un dispositivo malicioso que suplante al Times Frame. Mantén el dispositivo en una red local de confianza.

El API del dispositivo puede variar con el firmware. Si no devuelve `DeviceId` junto a `Channel/GetClockInfo`, el flujo falla de forma cerrada y no crea una integración sin validar.

## Desarrollo

El cliente HTTP está aislado en `custom_components/divoom_times_frame/api.py`; la entidad solo depende de su interfaz de operaciones y del coordinador de estado. Ejecuta las pruebas unitarias disponibles con:

```powershell
python -m unittest discover -s tests -v
```

Consulta [docs/roadmap.md](docs/roadmap.md) para el diseño de extensiones y futuras características.
