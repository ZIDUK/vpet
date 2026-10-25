# F2b: Integracion Del Crecimiento

**Objetivo:** activar en codigo la curva probada 200+8*IV y caps adultos
84/168/252, conservando genes/EV guardados y sin cargar hardware.
**Arquitectura:** dominio portable centralizado Python/C++; Pet calcula stats
y ganancias; Training/Exploracion/Items consultan ese contrato. Estadisticas
derivadas no agregan campos NVS. Pico conserva compatibilidad de imports.

## Contrato De Esta Revision

- El usuario autoriza continuar la integracion recomendada tras el piloto.
- Rangos adultos del perfil actual 1..3, independientes de nombres graficos.
  Mantener enums persistidos; huevos/bebes siguen sin entrenamiento directo.
- Preservar EV legacy hasta 252 aun por encima del cap actual; no rebajar ni
  gastar en ganancias sin efecto. Cuidado de bebes conserva reglas anteriores.
- Stat permanente maximo 320; margen temporal de combate hasta 448 (boost40%).
  HP/MP derivados maximos 680/330. Salud/energia de cuidado siguen 0..100.
- Rival Arena de referencia por rango: IV8, mitad del EV permitido, equipo
  2/3/4 compatible. No escala con cada entrenamiento del jugador ni aprende.
- No cambiar duracion/pausa de peleas, evolucion, identidad, sexo o breeding.
- No WiFi, flasheo, migracion destructiva ni edicion de arte generado.

## Pasos Y Pruebas

- [x] Tests rojos `tests/test_growth_integration.py`: stats de tres etapas,
  seis genes, EV legacy/snapshot, caps de todas las ganancias, parcial/bonus,
  rollback, chips sin efecto, boosts 264/320 y pools ampliados.
- [x] Contrato `core.growth`/`vpet/Growth.h`, integrar DNA/PetState/Nutrition;
  baseline legacy separado para conservar el experimento historico.
- [x] Training, previews y transacciones; Exploracion/guia y todos los EV
  recibidos; actualizar tests antiguos de cap global para sus nuevos limites.
- [x] Fighter/ConsumableEffects y sesiones Arena con rival por rango;
  paridad real Python/C++, consumo y fallo de guardado sin duplicaciones.
- [x] Training/Status legibles con tres digitos, barras acotadas a etapa y
  valores legacy; pruebas de pixeles existentes y nuevas vistas maximas.
- [x] Suite Python completa, nativas, build ESP32 y build de recursos si
  cambia catalogo generado. Documentar resultados, limites y aceptacion fisica.

Comandos: `.venv-platformio/bin/python -m pytest -q`,
`.venv-platformio/bin/pio test -d firmware/t-display -e native`,
`.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`.
Las pruebas nuevas compilan tambien un harness con PetState, Training y
consumibles reales. Sin instalacion ni lectura de partidas personales.

## Evidencia De Cierre: 2026-10-24

- Tests nuevos observados primero en rojo; la integracion de Python y C++
  pasa 57 pruebas especificas contando piloto y vistas. El harness reforzado
  comprueba 72864 valores Python activos y 12144 C++ contra referencia separada.
- SettingsStore real sobre KV de prueba: genes/EV legacy, schema 3 y
  estacionar/recuperar reserva conservados. Sin tocar NVS de la placa.
- Capturas de Training/Status inspeccionadas. 18 vistas amplias C++/Python
  identicas; comparacion visual existente completa aprobada tambien.
- Un mismatch de 10 pixeles en la suite existente detecto un draft obsoleto
  con EV legacy: Python decia +6 y C++ +0. Se acoto el aviso al margen real
  y se repitio la suite COMPLETA con directorio temporal exclusivo.
- Resultado final: 1752 Python aprobadas en 288.75 s; 185 nativas en 1.02 s.
- Build ESP32: aprobado en 9.56 s, RAM 56068/327680 y app 1031545/4194304.
  El aumento estatico de RAM es 16 bytes respecto a F1; no mide pico de heap.
- Recursos regenerados: 227 assets, payload 10891653 bytes, sin aumento.
- `git diff --check`, definiciones generadas y enlaces documentales verificados.
  Sin flasheo, commit/push ni cambios en el Hub paralelo.

Aceptacion fisica, balance prolongado de Arena y F2a siguen abiertos. Esta
entrega no autoriza cargar la placa ni reutilizar excepciones de Status previas.
