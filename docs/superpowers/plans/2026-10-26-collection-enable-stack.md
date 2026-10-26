# Reinicio Al Activar Coleccion

## Diagnostico Confirmado

El usuario reporta la pantalla de arranque al confirmar Enable. Captura serie
de la revision `c276f2f`: `Stack canary watchpoint triggered (loopTask)`.
ELF SHA-256 `0d0a5551f919a67997fd1aabfa21d64d2cce1e9808dd9912f6b9957a608f7684`.
El backtrace decodificado pasa por CollectionPanel::migrate,
CollectionStore::migrate, captureBody, SettingsStore::save/writeSnapshot y
SleepRoutine::encode. El fallo ocurre en la confirmacion que serializa el
estado, no simplemente al dibujar el primer boton. Captura local:
`out/collection-enable-verification/vpet-enable-live.log`.

Arduino configura una pila loopTask de 8192 bytes. El test previo permitia
3072 bytes por funcion, pero no limitaba la suma anidada con App, panel,
serializadores y biblioteca estandar. Las pruebas de host y el arranque
correcto no habian ejercitado esa pila limitada en la placa.

## Correccion

Metadatos temporales de migracion, guardado, cambio, fundador, cruce y avance
pasan a RAII con `unique_ptr` y `new (nothrow)`. El individuo temporal de la
migracion tambien deja la pila. Fallo de reserva bloquea la operacion; no
cambia el punto de commit, schema, bytes serializados ni reglas de dominio.
No aumenta la pila global ni cambia los recursos, render o preferencias.

RED: el limite reforzado de 1024 bytes por frame falla con maximo de 2496
en host. GREEN: 33 pruebas focalizadas aprobadas, incluidas transacciones,
fallos de persistencia, integracion App y visuales. Medicion Xtensa con los
comandos reales del build: migrate 2384 -> 304; saveActive 1712 -> 96;
activate 2288 -> 688; commitEgg 2416 -> 816 bytes por frame. El limite por
frame es una regresion preventiva, no una medicion de toda la pila en vivo.

Native: 185 aprobadas en 1.263 s. Firmware compilado en 9.176 s: RAM estatica
52236/327680, app 1102745/4194304. Advertencia existente TOUCH_CS.
Suite Python completa: 2038 aprobadas, 13278 advertencias existentes, 307.44 s.
Incluye Creator local solo como pruebas; no se publica en esta correccion.
Respaldo critico nuevo y app de 4 MiB en
`out/board-backups/20261026-enable-stack/`. SHA-256 app completa:
`04d3f71185305ec191e13ac70d3795e731960c6a7ea6e9515ac228a954302486`.
El prefijo de firmware respalda exactamente la revision `c276f2f`.

## Validacion En Placa

Usuario autoriza cargar solo el firmware corregido conservando partida y
confirmar el mismo la activacion. No activar Coleccion ni crear huevos por
el usuario. Tras cargar, verificar digest, arranque y capturar la activacion
fisica; hasta entonces el arreglo no se declara validado en hardware.

Carga firmware-only completada: `VPET_READY`, heap libre 90896/minimo 87524,
LittleFS 11804672/12451840, manifest 1. SHA-256 del firmware nuevo:
`7bc1cfea295c2bd7b2ab09a13bfd7c47f9cbaf9e02f6665cb8b3c1258aa61da1`.
Sin operaciones de activacion, fundador o breeding ejecutadas por el agente.
`verify_flash` confirma digest de firmware en 0x10000 y LittleFS conservado
en 0x410000 despues de la carga. El filesystem coincide tambien antes con
la copia completa extraida del respaldo de 16 MiB del 2026-10-25.
