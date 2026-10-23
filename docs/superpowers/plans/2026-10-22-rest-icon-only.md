# Descanso: Avisos Solo Con Iconos

## Solicitud

La foto IMG_4241.JPG de la placa muestra LOW ENERGY, 20/30 y una barra.
El usuario aclara que no desea textos. La entrega anterior habia retirado
la etiqueta solo para hora de dormir, no para poca energia.

## Alcance

- Quitar titulo, contador, barra y fondo negro de poca energia.
- Conservar unicamente el globo de gotas, incluida su variante de enojo.
- Hora de dormir conserva solo la carita dormida en su globo.
- Mismo cambio en Renderer.cpp y el overlay Home de sim_renderer.py.
- Sin cambios en Status, Training, Arena, cadencia, assets ni persistencia.
- Metas 30/35/40, horario aprendido, prioridades y ocultacion al dormir
  siguen siendo reglas internas, sin cambiar recuperacion ni balance.

## Verificacion

- Prueba roja sobre Renderer.cpp real: falla por etiquetas todavia presentes.
- Regresion exige ausencia de etiquetas y fondo intacto donde estaba el
  recuadro, ES/EN, izquierda/centro/derecha, animo normal/bajo y ambos
  motivos de dormir. El globo conserva sus pixeles, color y transparencia.
- Comparacion completa de sueno/cansancio actualizada para no esperar la
  barra antigua en ninguna de las cuatro etapas, conservando fondo y pies.
- El usuario autoriza esta carga sin repetir antes la validacion fisica
  pendiente de las cuatro paginas de Status. Esa aceptacion sigue abierta.
- 214 pruebas focalizadas y 185 nativas aprobadas; revision independiente
  sin hallazgos. Vista previa del renderer C++ real inspeccionada:
  `out/rest-icon-only/rest.png` y `bedtime.png`, sin texto ni recuadro.
- Firmware compilado: RAM estatica 56108/327680 (igual), app 1014997/4194304.
- Assets sin modificaciones; no es necesario volver a escribir LittleFS.
- Una corrida general encontro 1442 aprobadas y un fallo de edad 0 -> 1
  en el chequeo de no mutacion de Angry; ambas comparaciones de pixeles
  habian aprobado. Se congela monotonic solo durante esa prueba, como
  las otras pruebas de snapshots; no se cambia Pet ni su reloj real.
- Corrida general final: 1443 pruebas Python aprobadas en 251.94 s,
  incluidos Status, Training, Arena y comparaciones de pixeles. Se mantienen
  los avisos existentes de Pillow/pytest; no hay fallos. `git diff --check`
  limpio. Pruebas nativas: 185 aprobadas.

## Preparacion USB

Placa ESP32-D0WDQ6-V3 revision 3.1, ID 08f9e0d00788, flash 16 MB,
puerto `/dev/cu.usbserial-57040013171`.
Respaldo critico nuevo verificado, 24576 bytes:
`out/board-backups/20261022-rest-icon-only/08f9e0d00788-20261022-150215-critical.bin`.
SHA-256 `dad12e258392b241c01938569b4a80c3a1b37c6be957254cc8754b0ff0924215`.

SHA-256 del firmware preparado:
`5e0f689412fc3fb195023c5526c866a601dae3215c5770366ec134573aa62ee7`.
La verificacion en flash y el arranque se registran por separado.

Primer intento de carga: el puerto USB desaparecio despues del respaldo.
Esptool fallo al abrirlo (`No such file or directory`), antes de borrar o
escribir flash. Registro: `out/rest-icon-only/upload.log`. Se solicita
reconexion; este intento no cambia firmware, LittleFS ni NVS de la placa.

## Entrega Conjunta Posterior

El usuario reconecta USB y autoriza cargar ambas mejoras: estos avisos
sin textos y los menus atenuados por etapa. Se escribe solo firmware,
verificado por digest independiente; no se vuelve a escribir LittleFS
ni NVS. Esta entrega usa la imagen nueva
`529e7374819ff1859e3582be8e051a606b8b6d69938a16589fae237b00aacb22`,
no el binario preparado anterior. Respaldo, registros y verificacion de
arranque se documentan en
[Menus por etapa](2026-10-22-stage-menu-dimming.md).
