# Catalogo adoptado de consumibles vPet

Aprobado el 2026-10-15. Fuente: `src/core/adopted_items.py`.
Esta lista sustituye la propuesta de importar los 81 objetos sin filtrar.

## Reglas

- Carne y Proteina siguen ilimitadas exclusivamente en Alimentar.
- Nombres visibles completos y abreviados en MAYUSCULAS en ES/EN, tanto en Mochila como en Arena y recompensas. Las referencias originales conservan su escritura documental.
- HP/MP porcentuales se calculan sobre el maximo del luchador, no sobre salud de cuidado.
- Recuperacion: 20/50/90/100%; redondeo hacia abajo, minimo 1, sin superar el maximo.
- No resucita, no consume con recurso lleno y no cura fuera de combate.
- Discos: 20% o 40% sobre atributo inicial del combate; no acumulan. F2b local
  admite hasta 448 temporales sobre una base permanente de hasta 320.
- Un disco fuerte sustituye a uno debil; nunca se multiplica un bono anterior.
- Chips: +4 EV; alimentos de atributo: +2 EV; tope adulto por etapa
  84/168/252, sin alterar IV ni rebajar EV legacy. [Contrato F2b](growth-integration.md).
  El cap 252 del catalogo legacy generado es el limite de almacenamiento;
  las ganancias actuales respetan ademas el techo menor de la etapa.
- Venda cura lesion; Medicina cura lesion y recupera 20 de salud de cuidado.
- Manual: +1 EV en la siguiente sesion completada; no se acumula con Guia.

## Disponibilidad real

Catalogo, sprites, Mochila, bolsa de Arena y stock persistente integrados en sim y firmware.
La compilacion no equivale a validacion fisica: esta entrega no flashea la placa.
Las partidas conservan sus objetos legacy; no se reinterpretan ni renumeran.
No hay SQLite. JSON es un recurso de desarrollo; la placa usa constantes y LittleFS.

## Adquisicion y consumo

- Kit inicial una sola vez al crear/migrar el registro: 2 recuperadores pequenos, 2 discos MP pequenos, 1 venda, 1 disco OFF y 1 manzana azul.
- Una victoria de practica entrega 1 objeto, recorriendo este catalogo en orden, excluyendo comida ilimitada y stacks llenos.
- El cursor de recompensas se guarda con el stock. Derrota, empate, retirada y ticks repetidos del resultado no dan objetos.
- Limite 99 por objeto; Manual maximo 1. Reiniciar a huevo conserva stock y cursor; no repone el kit.
- Mochila permite cuidado, curacion de lesion y EV permanentes. Los objetos BAT solo se usan en Arena.
- Arena mantiene el reloj automatico al abrir la bolsa. No consume si el recurso esta lleno, el bono no mejora el actual o termino la pelea.
- Manual abre Entrenamiento sin gastarse: consume 1 al completar y guardar una sesion con hueco de EV. Guia antigua tiene prioridad; no se suman ambos bonos.
- Cancelacion o fallo de guardado conserva stock y efecto anterior. Premio de batalla con fallo de guardado permite Reintentar, sin duplicar el premio.

## Persistencia

Sim: `adopted_items` version 1, cantidades por ID y cursor, dentro del JSON reemplazado atomicamente.
ESP32: `adoptBag` y journal `itemTx` en NVS. Rechazo restaura el efecto; confirmacion pendiente
conserva el modelo y bloquea nuevas acciones hasta sincronizar y recuperar el journal;
un reinicio aplica los valores finales de forma idempotente antes de cargar la partida.
El schema principal sigue en 3 y no cambia ningun enum/indice antiguo. Registros desconocidos se rechazan en la placa sin borrar la partida.

## Objetos adoptados

| ID | Nombre | Referencia original | Categoria | Efectos vPet | Duracion | Sprite |
|---|---|---|---|---|---|---|
| `meat` | Carne | Meat | feeding | restore_care:h +20; weight:weight +1 | instant | [PNG](../assets/ui/items/adopted/meat.png) |
| `protein` | Proteina | vPet Protein | feeding | restore_care:e +20; weight:weight +2 | instant | [PNG](../assets/ui/items/adopted/protein.png) |
| `small_recovery` | Recuperador pequeno | sm.recovery | combat_recovery | restore_percent:hp +20 | instant | [PNG](../assets/ui/items/adopted/small_recovery.png) |
| `medium_recovery` | Recuperador mediano | med.recovery | combat_recovery | restore_percent:hp +50 | instant | [PNG](../assets/ui/items/adopted/medium_recovery.png) |
| `large_recovery` | Recuperador grande | lrg.recovery | combat_recovery | restore_percent:hp +90 | instant | [PNG](../assets/ui/items/adopted/large_recovery.png) |
| `super_recovery` | Recuperador completo | sup.recovery | combat_recovery | restore_percent:hp +100 | instant | [PNG](../assets/ui/items/adopted/super_recovery.png) |
| `mp_floppy` | Disco MP pequeno | MP Floppy | combat_recovery | restore_percent:mp +20 | instant | [PNG](../assets/ui/items/adopted/mp_floppy.png) |
| `medium_mp` | Disco MP mediano | Medium MP | combat_recovery | restore_percent:mp +50 | instant | [PNG](../assets/ui/items/adopted/medium_mp.png) |
| `large_mp` | Disco MP grande | Large MP | combat_recovery | restore_percent:mp +90 | instant | [PNG](../assets/ui/items/adopted/large_mp.png) |
| `super_veggy` | Verdura MP | Super veggy | combat_recovery | restore_percent:mp +100 | instant | [PNG](../assets/ui/items/adopted/super_veggy.png) |
| `double_floppy` | Disco doble | Double flop | combat_recovery | restore_percent:hp +50; restore_percent:mp +50 | instant | [PNG](../assets/ui/items/adopted/double_floppy.png) |
| `sweet_nut` | Nuez vital | Sweet Nut | combat_recovery | restore_percent:hp +100 | instant | [PNG](../assets/ui/items/adopted/sweet_nut.png) |
| `orange_banana` | Banana restauradora | Orange bana | combat_recovery | restore_percent:hp +100; restore_percent:mp +100 | instant | [PNG](../assets/ui/items/adopted/orange_banana.png) |
| `bandage` | Venda | Bandage | condition | cure:injured +1 | instant | [PNG](../assets/ui/items/adopted/bandage.png) |
| `medicine` | Medicina | Medicine | condition | cure:injured +1; restore_care:hp +20 | instant | [PNG](../assets/ui/items/adopted/medicine.png) |
| `off_disk` | Disco de ataque | Off. Disk | battle_boost | boost_percent:off +20 | one_battle | [PNG](../assets/ui/items/adopted/off_disk.png) |
| `def_disk` | Disco de defensa | Def. Disk | battle_boost | boost_percent:def +20 | one_battle | [PNG](../assets/ui/items/adopted/def_disk.png) |
| `speed_disk` | Disco de velocidad | Hispeed dsk | battle_boost | boost_percent:spd +20 | one_battle | [PNG](../assets/ui/items/adopted/speed_disk.png) |
| `omni_disk` | Disco integral | Omni Disk | battle_boost | boost_percent:off +20; boost_percent:def +20; boost_percent:spd +20; boost_percent:brn +20 | one_battle | [PNG](../assets/ui/items/adopted/omni_disk.png) |
| `super_off_disk` | Superdisco de ataque | S.Off.disk | battle_boost | boost_percent:off +40 | one_battle | [PNG](../assets/ui/items/adopted/super_off_disk.png) |
| `super_def_disk` | Superdisco de defensa | S.Def.disk | battle_boost | boost_percent:def +40 | one_battle | [PNG](../assets/ui/items/adopted/super_def_disk.png) |
| `super_speed_disk` | Superdisco de velocidad | S.speed.disk | battle_boost | boost_percent:spd +40 | one_battle | [PNG](../assets/ui/items/adopted/super_speed_disk.png) |
| `off_chip` | Chip OFF | Off. Chip | permanent | ev:off +4 | instant | [PNG](../assets/ui/items/adopted/off_chip.png) |
| `power_fruit` | Fruta de fuerza | Power fruit | permanent | ev:off +2 | instant | [PNG](../assets/ui/items/adopted/power_fruit.png) |
| `def_chip` | Chip DEF | Def. Chip | permanent | ev:def +4 | instant | [PNG](../assets/ui/items/adopted/def_chip.png) |
| `power_ice` | Hielo defensivo | Power Ice | permanent | ev:def +2 | instant | [PNG](../assets/ui/items/adopted/power_ice.png) |
| `spd_chip` | Chip SPD | Quick Chip | permanent | ev:spd +4 | instant | [PNG](../assets/ui/items/adopted/spd_chip.png) |
| `speed_leaf` | Hoja veloz | Speed Leaf | permanent | ev:spd +2 | instant | [PNG](../assets/ui/items/adopted/speed_leaf.png) |
| `brn_chip` | Chip BRN | Brain Chip | permanent | ev:brn +4 | instant | [PNG](../assets/ui/items/adopted/brn_chip.png) |
| `sage_fruit` | Fruta sabia | Sage Fruit | permanent | ev:brn +2 | instant | [PNG](../assets/ui/items/adopted/sage_fruit.png) |
| `hp_chip` | Chip HP | HP Chip | permanent | ev:hp +4 | instant | [PNG](../assets/ui/items/adopted/hp_chip.png) |
| `muscle_yam` | Tuberculo vital | Muscle Yam | permanent | ev:hp +2 | instant | [PNG](../assets/ui/items/adopted/muscle_yam.png) |
| `mp_chip` | Chip MP | MP Chip | permanent | ev:mp +4 | instant | [PNG](../assets/ui/items/adopted/mp_chip.png) |
| `calm_berry` | Baya serena | Calm berry | permanent | ev:mp +2 | instant | [PNG](../assets/ui/items/adopted/calm_berry.png) |
| `giant_meat` | Carne grande | Giant Meat | care | restore_care:h +40; weight:weight +2 | instant | [PNG](../assets/ui/items/adopted/giant_meat.png) |
| `sirloin` | Solomillo | Sirloin | care | restore_care:h +60; weight:weight +3 | instant | [PNG](../assets/ui/items/adopted/sirloin.png) |
| `digimushroom` | Champinon | Digimushrm | care | restore_care:h +15; weight:weight +1 | instant | [PNG](../assets/ui/items/adopted/digimushroom.png) |
| `blue_apple` | Manzana azul | Blue apple | care | restore_care:p +20 | instant | [PNG](../assets/ui/items/adopted/blue_apple.png) |
| `prickly_pear` | Pera ligera | Pricklypear | care | weight:weight -2 | instant | [PNG](../assets/ui/items/adopted/prickly_pear.png) |
| `training_manual` | Manual de entrenamiento | Trn. manual | training_boost | training_ev_bonus:trained_stat +1 | next_completed_training | [PNG](../assets/ui/items/adopted/training_manual.png) |

## Excluidos

Todas las fichas de evolucion; llaves, pruebas de misiones, pesca, herramientas de mapa y objetos de venta.
Tambien coma, estados de combate inexistentes, disciplina, cansancio y longevidad.
Los chips DV y alimentos de efectos vagos/riesgosos no se adoptan sin una regla concreta.

## Compatibilidad

El catalogo anterior de siete entradas es la capa de compatibilidad de partidas, no el catalogo futuro.
Tonico, Estrella, Amuleto y Botiquin no se convierten automaticamente a objetos nuevos.
Guia y Manual representan la misma mejora; su migracion debe evitar duplicar recompensas.

## Generacion

`.venv-platformio/bin/python scripts/export_adopted_items.py`
Usar `--check` para verificar JSON, documentacion, header y pixeles.
