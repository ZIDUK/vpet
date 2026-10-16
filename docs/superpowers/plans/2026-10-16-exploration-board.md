# Exploracion: port a T-Display

Autorizado el 2026-10-16: llevar el menu y ciclo del simulador a la placa.
Baseline dc6dfaf. No cambiar balance ni enums NVS existentes.

1. Portar Exploration puro: tres rutas, limites semanales, dos noches para
   Llama, Guia, preview y recibo unico. Vectores compartidos Python/C++.
2. Persistir un registro expState versionado dentro de PetState y snapshots
   atomicos. Snapshot v2 lee v1 sin reinterpretarlo; journals antiguos se
   recuperan antes de guardar v2. Swap/park conservan la expedicion de cada pet.
   Entrenamiento consume Guia antes que Manual, sin acumular bonos.
3. Portar sesion y tablas ES/EN a Panels.cpp. Barra de nueve iconos en sim y
   placa: Status, comida, entrenamiento, explorar, batalla, descanso, mochila,
   pedia y opciones. PanelId::Exploration se agrega al final; ningun enum
   persistido se renumera. Durante viaje se pausa cuidado/evolucion y las
   acciones no disponibles abren el viaje. Status sigue disponible.
4. Reloj: usar calendario civil, no millis para duraciones/semana. La placa
   no tiene RTC respaldado de alimentacion: tras perder la hora pedir ajuste
   mediante Fecha/Hora existentes; no fingir progreso offline. Guardar ultimo
   tiempo fiable con la mascota; impedir cobro/inicio con reloj no fiable.
5. Probar estados, limites, rechazo/Pending y recuperacion tras cada escritura,
   navegacion y render ES/EN a 240x135; comparar con el sim y compilar firmware.
6. Actualizar docs de alcance real. Regenerar assets, respaldar NVS, flashear
   firmware y LittleFS autorizados y verificar hashes, VPET_READY y heap.

Validacion visual fisica posterior requiere fotos/video o inspeccion real;
serial no demuestra todas las pantallas. No incluir nuevas especies, WiFi,
economia ni otras recompensas.

## Verificacion de software

- Suite completa final: 1067 passed, 6654 avisos existentes de Pillow/pytest,
  156.58 s. PlatformIO native: 172 casos aprobados.
- 162 vectores de recompensas Python/C++, incluyendo limites, cuidado pobre,
  tiempo parcial y aprendizaje/dominio. Pruebas de codec, snapshot v1/v2,
  swap/park y fallos/reintentos de persistencia.
- 127 casos de UI, con 361 renders de posiciones/estados ES/EN y las tres
  evoluciones de combate, sin pixeles fuera de 240x135 ni assets ausentes.
- App.cpp real en host: salida rechazada, cobro Pending y recuperacion sin
  duplicados, pausa de edad/hambre/energia y llamadas, Options Load durante
  llamada activa, reloj de otra mascota tras swap y timeout del asistente.
- Revision independiente aprobada tras corregir los casos de ciclo de vida.
- Firmware final: RAM 50188/327680; Flash 1006521/4194304 bytes.
- Assets regenerados: 176 archivos, 7467764 bytes. Capturas del renderer
  C++ de produccion inspeccionadas en out/exploration-board/gallery.png;
  no son fotografias de la placa.
- Dominio bajo ASan/UBSan: reglas, codec, persistencia, entrenamiento e
  interrupciones completados sin reportes.

## Despliegue USB comprobado

- Firmware y LittleFS cargados; `Deploy OK`, heap_free=72644,
  heap_min=72568, fs_used=8212480/12451840, manifest=1.
- esptool verify_flash: digest coincidente para firmware en 0x10000
  (1013104 bytes) y LittleFS en 0x410000 (12451840 bytes).
- Respaldo actual de NVS/particiones conservado localmente antes de cargar;
  no se borro NVS ni se reinicio la mascota deliberadamente.
- Arranque normal registrado en out/exploration-board-deploy/boot-final.log.
  Una apertura serial previa entro a DOWNLOAD_BOOT; se recupero con DTR/RTS
  desactivados antes de abrir el puerto y un nuevo reset. No se reflasheo
  ni se borraron datos para resolverlo.
- BLE anuncio y conecto. El arranque final registro PAIR_FAILED: la
  autenticacion desde el telefono no queda certificada en este despliegue.
  No se cambiaron perfil, radio ni WiFi como parte del port.
- La entrada de Exploracion esta en el cuarto icono (indice 3). Sin hora
  fiable se pueden consultar rutas; enviar o reclamar pide ajustar Fecha/Hora.
- Aceptacion visual fisica de los menus y prueba real de viaje/reinicio con
  el usuario siguen abiertas; los renders de host no son fotos del dispositivo.

SHA-256 de los artefactos instalados:

```text
firmware.bin  9d6fe561e948298ea7db9ca8181ade760d672b26bad89aa77f5b9a6ae70a7a7c
littlefs.bin  47574738a836ae667e29dfe66b424db20c7141e67c447c43a29ea15339310048
manifest.json 31c8238997cb8dce3f01a7b2b55bd8b1f9c3872cffeb585cdbfe589976bc9f42
```
