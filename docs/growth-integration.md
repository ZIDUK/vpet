# Crecimiento Por ADN Integrado

Revision: 2026-10-24. Continuacion autorizada de F2b. Integrado en codigo de
simulador y firmware, SIN nueva carga ni aceptacion fisica. F2a (identidad,
sexo y parentesco), roster, breeding y la pausa de Mochila no forman parte
de esta entrega.

## Reglas Activas En Esta Revision Local

- `core.growth` y `vpet/Growth.h` definen un perfil de tres rangos adultos.
  Los nombres y graficos no intervienen: otros paquetes del mismo perfil
  reutilizan las reglas. No admite topologias evolutivas arbitrarias todavia.
- Cada atributo usa SU IV (0..15) del ADN. Potencial final = `200+8*IV`;
  techo por rango = redondeo half-up de `potencial*rango/3`.
- EV permitidos por atributo: 84 / 168 / 252. Base y progreso dentro de
  cada rango siguen la formula del [piloto](growth-pilot.md).
- Firemon IV10 puede llegar a 93, Flamemon a 187, Dragfiremon a 280.
  IV0 termina en 200; IV15, en 320. No hay un techo universal de 99.
- Huevo/Sparkmon no acceden a entrenamiento directo ni Arena. Sus reglas
  previas de cuidado/pasivos y calculo de stats se conservan.
- Salud, hambre, energia y animo de crianza siguen en 0..100. HP/MP de
  combate son otros valores: maximos permanentes de 680/330 en este perfil.

## Conservacion De Partidas

El ADN y los seis EV conservan su formato y significado persistido. No se
agregan campos ni cambian enums numericos o schema NVS 3. Los stats se
recalculan, no se guardan como valores mayores en slots de un byte.

Un EV legacy de 252 en Firemon sigue guardado como 252: no se rebaja a 84.
Solo se usan hasta 84 para el stat actual. Al evolucionar se utiliza mas de
ese progreso, pero no se puede sumar EV nuevo mientras el guardado ya alcance
o supere el techo de la etapa. Por eso la pantalla puede mostrar `252/84`:
es progreso previo conservado, no una ganancia nueva ni un error de guardado.

Round-trip del guardado y estacionar/recuperar la reserva se prueban con el
SettingsStore real sobre almacenamiento de prueba. No se leyo ni migro la
partida personal de la placa; la aceptacion fisica sigue pendiente.

## Ganancias Y Gasto

Pet/PetState centralizan el limite: Training, menu corto, descanso, batallas
legacy, Exploracion, chips y otros objetos no pueden saltarselo. Restaurar
una partida no usa la misma operacion que sumar ganancias.

- Training de atributos conserva +6 EV, 8 energia y 10 s. La ultima
  repeticion puede ser parcial; solo se cobran repeticiones que suman EV.
- Llegar al techo bloquea la siguiente sesion, sin cobro ni llamada a guardar.
  Evolucionar abre el tramo siguiente; no reinicia ADN/EV.
- Manual/guia solo se gastan si queda espacio para SU bonus. Si la ganancia
  base llena el atributo, se conserva el bonus para otra sesion.
- Chips sin efecto y EXP con esfuerzo/EV de mente llenos no consumen stock.
- Exploracion muestra/cobra su recompensa real, nunca negativa cuando un
  EV legacy excede el techo. Un reinicio no convierte el mismo recibo en otro.
- Rollback de Training conserva tambien EV legacy, bonus, energia y stock.

14 repeticiones por atributo completan un tramo de 84 EV desde el cap anterior,
sin bonus/pasivos. Es tiempo activo de entrenamiento, no tiempo total de crianza.

## Combate E Interfaz

PetState y penalizaciones de peso devuelven uint16 para stats. Fighter admite
320 permanentes; bases de potenciadores tambien son uint16. Los productos
del perfil usan intermediarios anchos, sin truncar 264/320 a un byte.

Boosts de 20/40% reemplazan el porcentaje anterior sobre la base original,
sin acumular: 320 -> 384 -> 448. No rebajan a 99. El maximo temporal de 448
no cambia el potencial permanente ni los genes. Curacion porcentual usa el
pool ampliado y conserva las reglas de no consumir sin efecto.

Arena toma un rival de referencia por rango: IV8 y mitad de su EV permitido,
stats 61/108/156 y equipo de 2/3/4 tecnicas compatible con esa etapa. No copia
ADN/EV del jugador, no crece con cada entrenamiento suyo ni aprende. Es un
primer ajuste para que no siga con el rival fijo de 25; dificultad y experiencia
fisica aun por validar. Rondas, dano base, pausas y reglas de items por accion
no se modifican en esta entrega.

Training muestra el limite actual y barras acotadas, incluso con EV legacy.
El resumen usa la misma formula por rango que Pet (no una aproximacion vieja).
Status admite tres digitos y escala la barra al techo de cada gen/etapa;
las columnas no invaden unas a otras en la captura maxima comprobada.

## Evidencia Y Limites

- Nuevas pruebas de reglas observadas en rojo antes de la integracion.
- 12.144 puntos del PetState REAL coinciden con Python/candidato independiente
  al calcular stat, techo, limite EV y una ganancia; no solo un mock numerico.
- 72.864 valores del calculador Python activo (seis posiciones geneticas)
  coinciden tambien con esa referencia independiente.
- Pruebas de seis genes, tres etapas, exceso legacy, evolucion, parcial/bonus,
  chips, EXP, boosts, HP/MP, penalizaciones y ausencia de guardado sin efecto.
- SettingsStore real conserva schema, genes/EV y reserva, sin archivos NVS reales.
- 18 comparaciones pixel-perfect de Training real C++/Python: tres etapas,
  ES/EN y seleccion/preparacion/resumen con valores amplios y EV legacy.
- Status con seis stats de 320: numeros dentro de su columna y modelo sin mutar.
  El stub TFT no valida tipografia de Status en la pantalla fisica.
- Galerias inspeccionadas en `out/growth-integration/training-wide.png` y
  `out/growth-integration/status-320.png`.

La primera suite completa se interrumpio por falta de espacio local. Una
repeticion detecto ademas conflicto de limpieza entre directorios temporales
de pytest y un fixture antiguo de cap 252. Se aislaron los directorios y se
actualizaron pruebas de contrato, conservando casos de exceso legacy. El
resultado de cierre se registra en [estado del proyecto](project-status.md).

El [informe de laboratorio](growth-pilot.md) mantiene una formula legacy
explicita para comparar contra la anterior. Su marca de activacion indica
codigo local, NO despliegue en hardware. No anunciar esta curva en un video
de placa hasta cargar y aceptar fisicamente esa misma revision.
