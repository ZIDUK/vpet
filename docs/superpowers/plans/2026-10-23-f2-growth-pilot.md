# F2b Growth Pilot Implementation Plan

> Ejecucion inline con pruebas primero. Alcance aprobado por el usuario al
> continuar la recomendacion de simular/validar F2; no activar balance.

**Goal:** medir la curva 200+8*IV por rango adulto sin cambiar partida ni motor.
**Architecture:** calculador puro opt-in, referencia C++ portable no enlazada
al firmware, informe host que reutiliza PracticeBattle con combatientes de
laboratorio. No duplicar el motor ni simular premios/guardado.
**Tech Stack:** Python, C++17, pytest, motor de practica existente.

## Restricciones

- Perfil piloto soportado: 1..3 rangos adultos, IV 0..15, EV almacenado 0..252.
- Redondeo entero half-up; mismo resultado en Python/C++.
- No modificar DNA, Pet, entrenamiento, inventario, NVS, UI ni reglas activas.
- Huevo/Sparkmon no se vuelven entrenables; el piloto consume rangos, no nombres.
- Peleas sin items, peso, premios ni controlador temporal; tiempos son una
  proyeccion 500+(rondas-1)*1450 ms, no medicion fisica ni validacion de mochila.
- No flashear, publicar ni migrar partidas en esta fase.

## Tarea 1: Contrato Matematico

Archivos: `src/core/growth_pilot.py`, `tests/test_growth_pilot.py`.
API: `point(iv, ev, rank, ranks=3)` devuelve base/cap/stat/EV activo/EV guardado;
`project_training(iv, ev, rank, requested=6, ranks=3)` no reduce EV legacy y
solo propone coste si hay ganancia. Ambos rechazan entradas fuera del perfil.

- [x] Escribir tests de puntos ancla, redondeo, entradas invalidas, EV legacy,
  ultima repeticion parcial, bonus de 7 EV y cero coste al alcanzar el cap.
- [x] Ejecutar pruebas y comprobar fallo por API ausente.
- [x] Implementar enteros: P=200+8*IV; cap=round(P*r/R);
  CapEV=6*floor(252*r/(6*R)); base=round((10+3*IV)*(r+4)/5);
  stat=base+floor((cap-base)*min(EV,CapEV)/CapEV).
- [x] Barrer 16 IV x 253 EV x tres rangos; comparar formula activa,
  monotonia por EV/IV/evolucion y espacio nuevo por evolucion.

## Tarea 2: Referencia Cruzada Y Compatibilidad

Archivos: `firmware/t-display/lib/vpet_core/src/vpet/GrowthPilot.h`,
`tests/growth_pilot_trace.cpp`, `tests/test_growth_pilot.py`.

- [x] Test fallido que compile/ejecute referencia C++ independiente y compare
  cada punto y proyeccion de entrenamiento con Python.
- [x] Implementar referencia portable uint16 para stats y enteros anchos.
  No incluirla en PetState, App ni otro consumidor activo.
- [x] Comprobar partidas/snapshots sin mutacion y combatientes vigentes con 99.
- [x] Registrar como incompatibilidad esperada los boosts actuales sobre
  stats de laboratorio >99; no cambiar items como parte de este piloto.

## Tarea 3: Informe Y Regresion

Archivos: `scripts/growth_pilot.py`, `tests/test_growth_pilot.py`,
`docs/growth-pilot.md` y referencias de arquitectura/estado/roadmap.

- [x] Escribir pruebas de informe reproducible, pools HP/MP, presupuesto de
  repeticiones/energia/tiempo activo y fixtures de combate deterministas.
- [x] Implementar JSON/CSV en `out/growth-pilot/`, sin leer/escribir partidas.
  Escenarios iguales, desiguales, rival fijo actual y defensa extrema.
- [x] Ejecutar informe y revisar resultados; documentar limites y riesgos.
- [x] Ejecutar suite Python completa, nativas y build ESP32; diff/checks.
- [x] Mantener F2a y activacion/migracion de F2b abiertos hasta aprobar balance.

## Evidencia De Cierre

- Rojo: 18 fallos iniciales por modulos/CLI aun inexistentes. Primera
  compilacion del fixture C++ detecto namespace incorrecto de Element;
  se corrigio el fixture y se repitieron pruebas.
- Verde: 23 pruebas especificas en 4.14 s; 97.152 proyecciones identicas y
  cuatro trazas de combate Python/C++ con stats ampliados coincidentes.
- Informe: 12.144 puntos, cero perdida frente a legacy, cero retrocesos,
  218 encuentros; incompatible boost 264->99 y rival fijo no balanceado.
- Completa: 1710 Python aprobadas en 279.39 s; 185 nativas en 4.49 s.
  PlatformIO requirio acceso a su cache fuera del sandbox; no se hizo upload.
- Build ESP32 aprobado en 23.81 s; RAM 56052/327680,
  app 1030989/4194304. Conserva advertencias preexistentes de TFT/Pillow/pytest.
- `content_definitions.py --check` y `git diff --check` aprobados; F1 y
  cambios previos conservados. Sin migracion, radio, flasheo, commit ni push.
