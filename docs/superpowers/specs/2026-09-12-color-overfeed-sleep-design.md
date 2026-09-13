# COLOR Overfeed And Sleep Disturb

Primer corte de cuidado fino COLOR. Proteína, Effort hearts, lesión y
medkit quedan fuera. El menú sigue con 8 iconos.

## Goal

Con hambre llena se puede dar **una** comida extra por ciclo. Esa comida
no es care mistake. Despertar de noche **sí** suma un CM.

## Decisiones

| Tema | Valor |
|---|---|
| Ciclo | Hasta que HAM baje de 100 por decay |
| 1ª comida a HAM 100 | Overfeed: HAM sigue 100, peso +1, `overfeeds` +1, no CM |
| 2ª+ a HAM 100 | Feed no arranca. Carne en Items no gasta stock (`Blocked`) |
| Comida con HAM < 100 | Igual que ahora (+20 placa / +25 sim) |
| Disturbio | Rest despierta. Si hora 21:00–07:59 → +1 CM |
| Día | 08:00–20:59: despertar no suma CM |
| Huevo | Sin feed ni disturbio |
| Reset al evo | `overfeeds` y flag de ciclo a 0 |
| Persistencia | Schema 2, claves `overfed` (0/1) y `overfeeds`. Faltan → 0 |
| Status | Página 2 muestra `OF` |

## Fuera

Proteína, overdose, Effort hearts, batalla, saco, tumba, BLE mando.
