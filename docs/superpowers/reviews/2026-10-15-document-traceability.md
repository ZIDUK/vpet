# Auditoria de trazabilidad documental

Fecha: 2026-10-15. Baseline de codigo: `2e170322a2adced4d8335f97d4f245aa62a77d60`.
Se contrastaron documentos operativos y planes con el codigo, pruebas, indice
Git local y `git ls-remote origin refs/heads/master`. El remoto confirmo ese hash.

Actualizacion 2026-10-16: el usuario confirmo Status y autorizo continuar.
El flasheo y la correccion del pico de heap se registran en
[despliegue de placa](2026-10-16-board-deployment.md). Los apartados inferiores
conservan el corte de auditoria del dia 15, incluido el bloqueo que habia entonces.
Este informe se incorpora a la entrega documental junto con ese registro;
las reconciliaciones propuestas en la tabla no se dan por ejecutadas.

## Que significa trazabilidad

- Git: el documento tiene historial y esta incluido en el commit publicado.
- Funcional: requisito -> decision/spec -> implementacion -> prueba -> entrega.
- Fisica: evidencia observada en una placa identificada, ligada a un build.

La primera no demuestra las otras dos. Un documento historico correctamente
fechado no pierde trazabilidad por describir una version antigua.

## Resultado de Git

En el baseline hay 50 Markdown versionados bajo README/AGENTS, docs, .plan,
.claude y .archify. No habia cambios ni documentos oficiales sin seguimiento.
Tampoco aparecieron documentos ignorados bajo docs, .plan, .claude o .archify.
El HEAD local y master remoto coincidian: no habia un push documental pendiente.
Este informe es un documento nuevo posterior a ese baseline; no forma parte
del commit citado y no se debe afirmar publicado sin comprobar otro push.

## Documentos con trazabilidad funcional incompleta

Todos los archivos siguientes YA estan publicados. La accion propuesta es
corregir o delimitar su contenido, no volver a subirlos sin cambios.

| Documento | Hueco observado | Accion y sentido de publicarla |
|---|---|---|
| [README](../../../README.md) | La seccion Estado actual habla de dos paginas de Status y Carne gastable en Mochila. El runtime tiene cuatro paginas y Alimentar ilimitado separado del stock. | Actualizar el resumen con enlaces a contratos y pruebas actuales. Si: es la puerta de entrada del proyecto. |
| [Estado del proyecto](../../project-status.md) | El bloque denominado vigente conserva HEAD de63fd0, Arena a 1500 ms y exploracion no implementada. No enlaza la entrega 2e17032 ni los consumibles actuales. | Nuevo corte vigente; conservar debajo los cortes historicos fechados. Si: evita confundir pendientes reales con trabajo terminado. |
| [Roadmap de entrega](../plans/2026-10-11-delivery-roadmap.md) | Mezcla actualizaciones recientes con PlatformIO bloqueado, cambios sin commit, happy/sad sin integrar y catalogo nuevo pendiente. Algunas brechas visuales y de hardware SI siguen abiertas. | Reconciliar cada casilla con archivo/test/commit, conservando abiertas Arena visual y aceptacion fisica. Si: es el indice declarado vigente. |
| [Arquitectura](../../architecture.md) | Entrada anuncia repeticion de NEXT a 400/90 ms, mochila anterior y pesa pendiente en C++; otras secciones ya describen stock adoptado y journals. | Sustituir las descripciones contradictorias y enlazar Input.cpp, Panels.cpp, App.cpp y regresiones. Si: afecta futuras decisiones tecnicas. |
| [.plan/roadmap](../../../.plan/roadmap.md) | Presenta Pico/CircuitPython, 24 pruebas y sprites pendientes como roadmap sin etiqueta legacy. Compite con el indice de T-Display. | Marcar como historico y apuntar al roadmap vigente; no reescribir la historia como si fuera actual. Si: una correccion pequena evita dos fuentes de verdad. |
| [.plan/current-sprint](../../../.plan/current-sprint.md) | Se llama sprint actual pero corresponde a la reorganizacion Pico y no enlaza entregas recientes. | Rotular el corte historico y enlazar el indice vigente. Si; no inventar tareas actuales en el sprint antiguo. |
| [.plan/ideas](../../../.plan/ideas.md) | Mezcla propuestas sin aprobar con capacidades ya existentes, como simulador, personalidad e idiomas. No relaciona cada idea con decisiones posteriores. | Clasificar adoptada/descartada/futura y enlazar specs cuando existan. Si, pero prioridad menor; no implica implementar el parking lot. |
| [Contexto generado de Claude](../../../.claude/pipeline/project-doc.md) | Corte 2026-10-05; afirma que UI/NVS de practica estan incompletos. Una IA podria tomarlo como contrato actual. | Mantenerlo como snapshot fechado o regenerarlo con commit y referencias canonicas. Si, porque ya se distribuye con el repo; no publicar caches o credenciales nuevas. |
| [Notas de hardware](../../hardware-notes.md) | Conserva una intro no desplegada y una suspension de carga de un corte antiguo. No hay evidencia actual ligada al build nuevo. | Separar instrucciones estables del registro historico; agregar referencia al informe de despliegue solo despues de hacerlo. Si; nunca afirmar validacion visual desde serial. |
| [Flujo de desarrollo](../../development-workflow.md) | El aplazamiento de despliegue de 2026-10-05 esta entre instrucciones operativas. No explica el workaround local actual de PLATFORMIO_CORE_DIR. | Delimitar esa nota como historica y documentar el workaround como opcional/local, no requisito universal. Si: mejora reproduccion sin modificar permisos globales. |
| [Conectividad](../../connectivity.md) | Describe VPET_READY como heap anterior a activar BLE. main.cpp ahora lo emite despues de inicializar App y restaurar la configuracion BLE. | Corregir el significado de la telemetria; mantener conexion/reconexion de telefono como validacion independiente. Si: cambia la interpretacion de mediciones. |
| [Plan de alimentacion y peso](../plans/2026-10-14-feeding-weight-combat-evolution.md) | Estado y casillas pendientes conservan el bloqueo PlatformIO y cifras anteriores. Faltan enlaces de cierre a pruebas actuales y catalogo adoptado. | Agregar cierre por tarea con evidencia, sin convertir propuestas en balance fisico demostrado. Si: el codigo ya tiene implementacion comprobable. |
| [Contrato de entrenamiento](../../training-session.md) | Save failure equivale siempre a rollback. El firmware actual distingue rechazo de intent aceptado pendiente; App bloquea acciones y recupera sin duplicar. | Aclarar rechazo/pendiente/confirmado y enlazar las pruebas de almacenamiento/App. Si: es un contrato activo, no solo historia. |

## Historia o propuestas que no deben confundirse con fallos

- [.archify](../../../.archify/architecture-vpet-20261005/README.md) declara
  explicitamente su commit fuente `3b98843c...` y recibos de validacion. SI tiene
  procedencia: es una fotografia anterior, no la arquitectura actual. Mantener
  ese corte; generar otro si se quiere una vista actualizada.
- [Catalogo DW1 de referencia](../specs/2026-10-14-digimon-world-1-items.md)
  indica fuente, fecha, 128 referencias y exclusiones; enlaza al subconjunto
  adoptado. No activar todos sus objetos ni borrar las referencias de evolucion
  de esta copia historica como si fueran objetos disponibles.
- [Consumibles adoptados](../../adopted-items.md) SI enlaza fuente, sprites,
  efectos, adquisicion, limites y persistencia. Lo pendiente es aceptacion fisica,
  no crear otra base de datos ni publicar otra lista paralela.
- [Exploracion](../../exploration.md) distingue sim implementado de port C++
  pendiente. Flashear este firmware no incorpora un motor de exploracion de
  placa que todavia no existe.
- [Negocio posterior a la placa](../plans/2026-10-13-mall-business-plan.md)
  SI pertenece a vPet, enlaza el roadmap y se declara futuro. Sus entregables
  aun no tienen codigo/pruebas porque no estan implementados; no es un archivo
  ajeno para eliminar ni autoriza app, WiFi o evento.
- [Paquetes](../../content-packages.md), [seguridad](../../security.md), planes
  fechados y docs/legacy conservan valor como propuestas o historia. No marcar
  instalador, firmas, OTA o produccion como implementados sin evidencia nueva.

## Evidencias locales y privacidad

`out/`, previews, build-tdisplay, LittleFS y .pio se excluyen deliberadamente.
Los planes que solo apuntan a una captura en out no entregan esa captura a otro
clon. Conviene publicar una seleccion pequena y saneada de capturas/logs, con
commit y procedimiento de reproduccion; no toda la carpeta de trabajo.

Nunca publicar dumps NVS, partidas, backups de flash, credenciales, caches,
procesos de brainstorm con tokens o binarios generados por simple limpieza.
`out/board-backups/` se conserva localmente; no debe borrarse ni pushearse.

## Verificacion de esta pasada y limite del despliegue

- Python completo: 769 passed, 6514 avisos de deprecacion, 151.78 s.
- PlatformIO native: 172 casos aprobados.
- Build ESP32 aprobado: RAM 50020/327680, Flash 990257/4194304 bytes.
- Assets regenerados: 162 archivos, 7162780 bytes; LittleFS compilado.
- Preflight USB: ESP32-D0WDQ6-V3, flash fisica 16 MB, presupuesto LittleFS
  7203959/12451840 bytes. No es una comprobacion del contenido instalado.
- Flasheo pendiente de la confirmacion/evidencia de las cuatro paginas de
  Status que exige AGENTS.md. Se solicito al usuario durante esta pasada.
  No se escribio firmware ni LittleFS y no se certifica contenido nuevo en placa.

SHA-256 del build preparado, no del contenido leido de la placa:

```text
firmware.bin  4cdda51b4056bfdbae6ef22d02f98f4094592601332eecf0abeafad472b95480
littlefs.bin  bd3677c7a31d3048d8ca8778f63d391280703ef7577b8d792abcc073086594fb
manifest.json faa0c3919b1a39f7ef75731861c590cc49acbbee182e8179e9e596b9967a2409
```

Recomendacion: publicar las correcciones documentales y este informe en un
commit especifico, despues de reconciliar los documentos; no agregar todo lo
ignorado ni confundir push con implementacion o aceptacion de hardware.
