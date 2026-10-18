# Hoja de ruta y guía de extensión

Este documento resume la arquitectura inicial y propone cómo añadir funciones a la integración Divoom Times Frame sin acoplar la lógica del dispositivo a las entidades de Home Assistant.

## Identidad del dispositivo y DeviceID

Durante el alta, el usuario introduce la IP y el DeviceID numérico asociado a su dispositivo Divoom. La integración consulta el endpoint local `Channel/GetClockInfo` y compara el `DeviceId` de la respuesta con el valor introducido. Si no puede obtener el identificador o no coincide, rechaza la configuración. También repite la comprobación al consultar el estado y antes de ejecutar comandos, para detectar si la IP termina apuntando a otra pantalla. Esta verificación evita errores de configuración y ayuda a que futuras funciones se dirijan al dispositivo correcto.

El DeviceID debe conservarse sin modificaciones en la entrada de configuración. Es el identificador estable para el registro de dispositivos de Home Assistant y es relevante para futuras funciones que puedan interactuar con Divoom Cloud. Un identificador localmente verificado no equivale a iniciar sesión en la nube ni concede permisos cloud por sí solo; esas funciones deberán definir su autenticación, almacenamiento seguro y manejo de caducidad de tokens antes de implementarse.

La verificación actual es una comprobación de identidad funcional, no autenticación criptográfica: la API local observada usa HTTP sin credenciales. Un servicio malicioso en esa IP podría imitar la respuesta. Por eso se recomienda una LAN de confianza y no exponer el puerto del dispositivo a Internet.

## Arquitectura actual

- `config_flow.py`: solicita IP, DeviceID y puerto opcional (por defecto `9000`), valida el formato y comprueba la identidad antes de crear la entrada.
- `api.py`: concentra el transporte local, el formato GET con JSON, la comprobación de errores de respuesta y los comandos disponibles.
- `__init__.py`: administra el cliente y el coordinador de estado por entrada, configuración inicial y descarga de plataformas.
- `light.py`: adapta energía y brillo a la API de entidad `light` de Home Assistant.
- `models.py` y `helpers.py`: tipos de estado y conversiones/validaciones puras que se pueden probar sin Home Assistant.

La API local conocida usa `http://<ip>:9000/divoom_api` con un cuerpo JSON que contiene `Command`. La pantalla usa comandos separados para consultar estado, modificar brillo y encender/apagar. Mantener el transporte en `api.py` permite ajustar método, ruta o respuestas de firmware en un único lugar.

## Cómo añadir una característica

1. **Verificar el protocolo** para el modelo y firmware de Times Frame; distinguir el API local del API cloud y documentar el comando y el esquema de respuesta observados.
2. **Añadir una operación tipada a `api.py`**. No enviar HTTP directamente desde una entidad. Validar explícitamente la respuesta y levantar un error de integración cuando falle.
3. **Elegir la entidad de Home Assistant adecuada**: `switch` para un conmutador independiente, `number` para un valor continuo, `select` para opciones enumeradas, `button` para acciones puntuales, o un servicio para operaciones con argumentos.
4. **Registrar la plataforma o servicio** en el ciclo de vida de la integración y asociar las entidades al DeviceID existente.
5. **Probar** la composición del comando, la traducción de escalas/unidades, las respuestas inválidas, errores de red y la descarga/reconfiguración de la entrada.
6. **Actualizar README y traducciones**, y describir permisos, alcance cloud/local y limitaciones de firmware.

## Candidatos para futuras funciones

La prioridad debe fijarse según comandos confirmados en Times Frame, no solo por comandos de otros modelos Divoom.

- Selector de watchface/cara si el firmware ofrece una lista de opciones y un comando de selección fiables.
- Botones para acciones puntuales como reinicio, con confirmación y advertencias cuando la acción interrumpa el dispositivo.
- Sensores para información que el dispositivo exponga localmente (por ejemplo, estado de iluminación o datos ambientales), si son útiles y estables.
- Servicios para enviar mensajes u operaciones con parámetros, con validación de longitud, color y límites del protocolo.
- Funciones de galería/fotos o sincronización con Divoom Cloud, únicamente después de confirmar los endpoints, el mecanismo de autenticación y qué operaciones están realmente disponibles para Times Frame.

## Criterios de diseño

- Reutilizar el cliente y el coordinador por dispositivo; no duplicar transporte ni sondeo por entidad sin necesidad.
- Evitar iniciar sesión o hacer llamadas cloud desde la ruta local de control.
- No registrar contraseñas, tokens ni cuerpos sensibles de solicitudes.
- No ocultar errores de red, respuestas con error o estados imposibles; exponer indisponibilidad a Home Assistant.
- Añadir entidades solo cuando exista soporte verificado en Times Frame y una semántica clara para Home Assistant.
