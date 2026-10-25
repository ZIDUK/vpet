# Piloto De Crecimiento Por ADN

Registro del piloto: 2026-10-23. La [integracion F2b del 2026-10-24](growth-integration.md)
ya esta activa EN CODIGO LOCAL, no en la placa. Las observaciones siguientes
describen el piloto previo; los bloqueos resueltos y limites actuales estan
en ese documento. El comando de informe conserva el baseline anterior.

Revision original: 2026-10-23. Implementacion experimental de F2b, NO balance activado.
Continuacion autorizada de la simulacion recomendada tras F1. F2a (identidad,
sexo, parentesco) y la integracion/migracion de F2b siguen pendientes.

## Contrato Y Arquitectura

- `src/core/growth_pilot.py`: calculador puro opt-in, sin importar Pet ni
  guardar estado. `point` y `project_training` usan solo enteros.
- `firmware/t-display/lib/vpet_core/src/vpet/GrowthPilot.h`: referencia
  portable del candidato, probada con compilador host. No esta incluida por
  PetState, Motion, App o el firmware ejecutado. Stats uint16 y productos uint32.
- `scripts/growth_pilot.py`: barrido, comparacion y combates host reproducibles,
  sin leer partidas de usuario. Reutiliza PracticeBattle, no otro motor.
- `tests/growth_pilot_trace.cpp`: referencia de vectores numericos y trazas
  del motor C++ existente con combatientes de laboratorio.
- La formula vigente de `dna.combat_stat`/PetState y su techo 99 no cambian.
  No hay nuevos campos persistidos, enums, recursos, UI, radio ni flasheo.

Perfil acotado a 1..3 rangos adultos, IV entero 0..15 y EV entero 0..252.
El informe calibra tres rangos adultos; huevo/Sparkmon no son rangos entrenables.
No se promete soporte de una topologia arbitraria de paquetes. Valores
invalidos se rechazan; no se convierten silenciosamente ni se genera ADN nuevo.

```text
P = 200 + 8*IV
CapStat = round_half_up(P*r/R)
CapEV = 6*floor(252*r/(6*R))
Base = round_half_up((10+3*IV)*(r+4)/5)
ActivoEV = min(EV_guardado, CapEV)
Stat = Base + floor((CapStat-Base)*ActivoEV/CapEV)
```

No se combina con el antiguo candidato de EV 192+4*IV. El ADN modifica el
potencial visible; todos tienen las mismas oportunidades de EV por etapa.

| IV | Firemon cap | Flamemon cap | Dragfiremon cap |
| --- | ---: | ---: | ---: |
| 0 | 67 | 133 | 200 |
| 8 | 88 | 176 | 264 |
| 10 | 93 | 187 | 280 |
| 15 | 107 | 213 | 320 |

Un Firemon IV0 terminaria en 67 por su potencial y etapa; no se garantiza
que todos superen 99 en cada forma. La diferencia es que 99 deja de ser un
techo universal y cada evolucion abre un techo mayor. No se renuevan los EV.

## Progreso Y Entrenamiento

No se descarta EV legacy superior al cap de una etapa: permanece guardado,
participa hasta el limite activo y vuelve a contar cuando se desbloquea.
La proyeccion nunca resta EV, incluso con 252 guardados en el primer rango.
Si no hay espacio nuevo, no propone gastar energia; la ultima repeticion
parcial cobra una sesion completa, igual que el contrato vigente. Se prueba
tambien una ganancia de 7 EV para el bonus, sin implementar su consumo.

| Rango | CapEV | Reps desde cero | Reps desde cap anterior | Energia desde cero | Tiempo activo desde cero |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 84 | 14 | 14 | 112 | 2 min 20 s |
| 2 | 168 | 28 | 14 | 224 | 4 min 40 s |
| 3 | 252 | 42 | 14 | 336 | 7 min |

Valores POR ATRIBUTO, usando +6 EV, 8 energia y 10 s de animacion. Los seis
atributos completos requieren 252 repeticiones, 2016 energia y 42 min de
animaciones. Esto NO es tiempo real de crianza: faltan descanso, navegacion,
comida, evolucion y disponibilidad. Los menus cortos de +1 EV tampoco se
convierten en el mismo coste ni eluden sus limites actuales.

## Resultados Matematicos

- Barrido escalar de tres rangos: 16 IV x 253 EV x 3 = 12.144 puntos.
  Cada stat usa esa misma funcion con su gen; no son todos los genomas posibles.
- Cero valores inferiores a la formula vigente y cero retrocesos al evolucionar
  en ese perfil. Monotonia por EV y por IV comprobada tambien en pruebas.
- 6.301 puntos superan 99. La formula vigente llega exactamente a 99 en
  1.010 puntos del mismo barrido.
- 1.616 incrementos de UN EV no mueven el entero visible. Es redondeo, no
  perdida del EV guardado; revisar como se explica el progreso al jugador.
- Mayor salto entre rangos: +107 en un stat. Incluye partidas con EV ya
  maximizados antes de evolucionar; no debe anunciarse como una mejora pequena.
- Paridad Python/C++: 97.152 proyecciones (perfiles 1/2/3, todos sus rangos,
  16 IV, 253 EV y ganancias solicitadas 1/6/7/252).

La conservacion anterior es numerica sobre el dominio valido actual, NO una
migracion NVS validada ni garantia para curvas/genes futuros. Antes de activar
hay que probar snapshots reales y reserva, con respaldo y esquema compatible.

## Combates Exploratorios

218 encuentros deterministas: dos modelos, tres rangos, cuatro IV (0/8/10/15),
tres niveles de EV, rivales iguales/fijo/mas fuerte y dos extremos defensivos.
Equipo por rango de 2/3/4 tecnicas, dominio 0, personalidad ofensiva, vinculo
50 y elemento fuego. Predominan stats simetricos; no equivale a cubrir todos
los estilos, mezclas de genes, pesos, emociones, items o especies.

Se evita el clamp 99 SOLO en los combatientes host del piloto. No se modifica
el constructor de combate del producto. Cuatro trazas adicionales de casos
altos/desiguales/defensivos coinciden ronda por ronda entre Python y C++.

| Rival | Mediana rondas vigente | Mediana rondas piloto | Empates vigente / piloto |
| --- | ---: | ---: | ---: |
| Igual | 7 | 9 | 2 / 1 de 36 |
| Fijo de Arena | 3 | 2,5 | 0 / 0 de 36 |
| Mas fuerte | 4 | 4 | 0 / 0 de 36 |
| Extremo defensivo | 30 | 30 | 1 / 1 de 1 |

Tiempos solo proyectados con 500+(rondas-1)*1450 ms, sin pulsaciones ni latencia:
9 rondas son 12,1 s. El rival fijo puede caer en una ronda en el piloto.
El limite actual de 30 rondas da como maximo 42,55 s programados, incluso un
empate. Por eso subir stats no resuelve el uso de Mochila ni valida el objetivo
de 45-90 s. Incluso 9 rondas a 2500 ms darian 20,5 s, no 45 s.

Recomendacion: primero pausa local de decision al abrir Mochila y coste de
una accion por objeto; despues calibrar rivales y ritmo con pruebas de curas,
empates y extremos. No inflar HP ni asegurar 45-90 s en cada encuentro.

## Bloqueos Antes De Activar F2b

1. Aprobar coeficientes, saltos al evolucionar y esfuerzo por etapa tras ampliar
   simulaciones de perfiles mixtos, tecnicas, peso y rivales apropiados.
2. Ampliar `PetState::combatStat/effectiveCombatStat`, `Nutrition::effectiveStat`
   y previews de Training, actualmente uint8/clamp99; revisar todos los callers.
3. El constructor Fighter limita a 99 en ambas plataformas. Los boosts actuales
   tambien: el probe real host `off_disk` baja 264 a 99 y consume una unidad.
   Es una incompatibilidad con el candidato, no una nueva ruta activa del juego.
4. `practice::Fighter::itemBase` es uint8; 264 no cabe aunque se quite el clamp.
   El mayor boost actual de 40% sobre 320 seria 448; requiere margen temporal
   superior al techo permanente. El laboratorio sin items admite hasta 320.
5. HP/MP de combate alcanzan 680/330 sin boosts. No son salud/energia de
   cuidado. Curacion host permanece acotada, pero faltan paridad completa de
   consumibles, cantidades sin efecto, recuperacion tras fallo y stock persistido.
6. Revisar escalas, numeros y barras de Status/Training; algunas normalizan a
   99. Revisar serializacion, exportaciones y futuros mensajes BLE antes de
   ampliar el contrato; no basta sustituir una etiqueta.
7. Conectar caps a TODAS las fuentes de EV (Training, Arena, descanso,
   Exploracion, chips/bonus) y a previews/confirmacion. Este piloto no modifica
   esas rutas ni sus reglas de gasto/guardado.

## Reproduccion

```sh
.venv-platformio/bin/python scripts/growth_pilot.py --out out/growth-pilot
.venv-platformio/bin/python -m pytest -q tests/test_growth_pilot.py
```

Salidas: `report.json` con supuestos, hashes de fuentes, resumen y encuentros;
`stats.csv` con 12.144 filas; `battles.csv` con 218 encuentros. Archivos en
`out/` son evidencia regenerable, no partidas ni balance configurado.
El comando propaga errores de lectura/escritura; una salida interrumpida no
es una entrega transaccional y debe regenerarse. No modifica inventario/NVS.

Pruebas nuevas observadas primero en rojo por APIs ausentes; despues pasan
23 pruebas especificas. La referencia C++ se compila con warnings como errores.
La ejecucion completa y el build se registran al cierre en
[estado del proyecto](project-status.md).
