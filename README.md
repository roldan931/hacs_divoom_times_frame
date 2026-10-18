# Divoom Times Frame para Home Assistant

Integración personalizada para controlar un Divoom Times Frame desde Home Assistant. Se comunica con la API HTTP local del marco, por lo que no necesita una cuenta, contraseña ni conexión a Divoom Cloud para los controles disponibles actualmente.

## Entidades y controles creados

La integración crea un dispositivo de Home Assistant llamado con el nombre que informa el Times Frame y una entidad:

| Entidad | Nombre visible | Controles |
| --- | --- | --- |
| `light.<nombre_dispositivo>_<nombre_de_pantalla>` | Pantalla (español) / Display (inglés) | Encender, apagar y ajustar el brillo |

Por ejemplo, si el dispositivo se llama **Times Frame Oficina** y Home Assistant está en español, la entidad será similar a `light.times_frame_oficina_pantalla`; en inglés, el sufijo visible puede ser `display`. El identificador exacto depende del nombre comunicado por el dispositivo, del idioma de Home Assistant y de si ya existe otra entidad con el mismo ID. Se puede consultar o cambiar en **Ajustes → Dispositivos y servicios → Entidades**.

**«Pantalla» es una entidad `light`, no una entidad `switch` separada.** Se usa `light` para poder ofrecer el encendido/apagado y el control de brillo en un solo lugar. El control de encendido del panel de Home Assistant actúa como interruptor.

### Servicios de Home Assistant

Usa los servicios `light.turn_on` y `light.turn_off` con la entidad de tu dispositivo:

```yaml
action: light.turn_on
target:
  entity_id: light.times_frame_oficina_pantalla
data:
  brightness: 128
```

El brillo que recibe Home Assistant está en el rango `0–255`; la integración lo convierte al rango `0–100` que utiliza el Times Frame. Se puede encender sin especificar brillo:

```yaml
action: light.turn_on
target:
  entity_id: light.times_frame_oficina_pantalla
```

Para apagar la pantalla:

```yaml
action: light.turn_off
target:
  entity_id: light.times_frame_oficina_pantalla
```

Home Assistant consulta el estado de encendido y el brillo del marco cada 30 segundos. Los cambios hechos desde Home Assistant vuelven a consultar el dispositivo para actualizar la entidad.

## Instalación con HACS

1. En HACS, abre **Integraciones** y selecciona **Repositorios personalizados**.
2. Añade `https://github.com/roldan931/hacs_divoom_times_frame` con la categoría **Integración**.
3. Descarga **Divoom Times Frame** y reinicia Home Assistant.
4. Ve a **Ajustes → Dispositivos y servicios → Añadir integración** y selecciona **Divoom Times Frame**.

## Configuración

Durante el alta, Home Assistant solicita:

- **Dirección IP** del Times Frame en la red local.
- **DeviceID** numérico del dispositivo Divoom.
- **Puerto**, opcional; si se deja vacío se utiliza `9000`.

La integración consulta `Channel/GetClockInfo` en la IP indicada y compara el `DeviceId` que devuelve el dispositivo con el valor configurado. Solo termina el alta cuando coinciden. Si el marco no responde, no informa un DeviceID o el ID es distinto, Home Assistant rechaza la configuración. La identidad también se comprueba al leer el estado y antes de enviar controles.

El DeviceID se conserva como identificador estable del dispositivo en Home Assistant y podrá servir para futuras funciones relacionadas con Divoom Cloud. La versión actual usa solamente la API local: introducir el DeviceID no inicia sesión en la nube ni autentica solicitudes cloud.

## Comunicación y seguridad

La integración se comunica con `http://<ip-del-marco>:9000/divoom_api` mediante solicitudes `GET` con un cuerpo JSON, que es el formato observado para el API local del Times Frame. Los comandos implementados actualmente consultan el estado, cambian el brillo y encienden o apagan la pantalla.

La API local observada usa HTTP sin autenticación. La comprobación del DeviceID permite detectar una IP mal configurada o que responda otro Times Frame, pero **no es una credencial ni una prueba criptográfica de identidad**. Mantén el marco en una red local de confianza y no expongas su puerto directamente a Internet.

La compatibilidad depende del modelo y del firmware. Si el dispositivo no devuelve el DeviceID en `Channel/GetClockInfo`, la integración falla de forma cerrada; no continúa sin verificar la identidad.

## Problemas frecuentes

- **No se puede conectar:** confirma que Home Assistant y el marco están en la misma red, que la IP es correcta y que el puerto configurado corresponde al API local (por defecto, `9000`).
- **El DeviceID no coincide o no se recibió:** comprueba el ID del Times Frame y que la IP apunta al marco esperado. El alta no se permite sin esta comprobación.
- **La entidad no aparece como `switch`:** es lo esperado; el control se crea como `light` para poder incluir el brillo. Su nombre visible es **Pantalla**.

## Desarrollo y futuras funciones

El cliente HTTP se encuentra en [api.py](./custom_components/divoom_times_frame/api.py); la entidad de Home Assistant está en [light.py](./custom_components/divoom_times_frame/light.py). Para ver las decisiones de arquitectura y propuestas de controles futuros, consulta [docs/roadmap.md](./docs/roadmap.md).

Las pruebas unitarias se ejecutan con:

```powershell
python -m unittest discover -s tests -v
```
