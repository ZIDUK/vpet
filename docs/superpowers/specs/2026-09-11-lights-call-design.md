# Lights Call

Cierra el Call de cría COLOR: a la hora de dormir, si la mascota no está
acostada, pide luces. Rest apaga la llamada. Ignorarla suma un care mistake.

## Decisiones

| Tema | Valor |
|---|---|
| Noche | 21:00–07:59 |
| Día | 08:00–20:59 |
| Contestar | icono Rest (ya es “luces off”) |
| Margen luces | 60 min / `CARE_TIME_SCALE` (placa 1 h, sim 600 → 6 s) |
| Hambre/fuerza | siguen 10 min / scale |
| Una vez por noche | tras start, miss o Rest no se relanza hasta el día |
| Prioridad | un call a la vez; hambre/fuerza ya activos no se sustituyen |
| Huevo | sin call |
| Persistencia | `call` NVS ya guarda el enum; `Lights=3` |

## Reloj

`updateCall` recibe `hour` (0–23) y `asleep`. El firmware toma la hora
local del ESP32; el sim usa el datetime de servicios. Default de tests:
hora 12, despierto.

## Fuera de este corte

Batalla, saco, tumba, overfeed, BLE mando, idle triste.
