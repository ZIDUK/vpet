# Objetos legacy y compatibilidad de partidas vPet

Version 1. Oficializado el 2026-10-14. Generado desde `src/core/item_catalog.py`
por `scripts/export_item_catalog.py`. Actualizar la fuente y regenerar; no editar esta ficha a mano.

El catalogo adoptado esta en [Consumibles vPet](adopted-items.md).
Estas siete entradas documentan el runtime anterior y sus partidas; no son el catalogo futuro.
Los objetos y fichas de evolucion estan excluidos de ambos catalogos.

## Lista oficial

| ID estable | ES / EN | Familia | Stock / limite | Origen | Sprite |
|---|---|---|---|---|---|
| `meat` | CARNE / MEAT | Alimentacion | Ilimitado | Menu Alimentar, ilimitado | [PNG](../assets/ui/items/meat.png) |
| `energy` | TONICO / TONIC | Recuperacion | 2 inicial; max. 99 | Kit inicial; sin reposicion repetible | [PNG](../assets/ui/items/energy.png) |
| `exp` | ESTRELLA / STAR | Esfuerzo (legacy) | 1 inicial; max. 99 | Kit inicial; sin reposicion repetible | [PNG](../assets/ui/items/exp.png) |
| `ring` | AMULETO / AMULET | Animo | 1 inicial; max. 99 | Kit inicial; sin reposicion repetible | [PNG](../assets/ui/items/ring.png) |
| `protein` | PROTEINA / PROTEIN | Alimentacion | Ilimitado | Menu Alimentar, ilimitado | [PNG](../assets/ui/items/protein.png) |
| `medkit` | BOTIQUIN / MEDKIT | Recuperacion | 1 inicial; max. 99 | Kit inicial; sin reposicion repetible | [PNG](../assets/ui/items/medkit.png) |
| `guide` | GUIA / GUIDE | Mejora de entrenamiento | 0 inicial; max. 1 | Jornada completa con buen cuidado (simulador y T-Display) | [PNG](../assets/ui/items/guide.png) |

## Fichas estandarizadas

Las fichas cubren los 12 campos aprobados. Descripciones y nombres estan disponibles en ES/EN.

### CARNE / MEAT

Carne asada para saciar el hambre y ganar peso.

Roasted meat that restores hunger and increases weight.

![CARNE](../assets/ui/items/meat.png)

| Campo | Definicion |
|---|---|
| ID | `meat` (indice de interfaz 0) |
| Categoria | Alimentacion |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemMeat`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | CARNE / MEAT; descripciones arriba |
| Stack maximo | Ilimitado en Alimentar; stock antiguo conservado sin uso |
| Efecto tipado | `restore`; `weight` |
| Objetivo | `h`, `weight` |
| Magnitud | h +20 (tope 100); weight +1 (tope 99) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `feeding`, `home`, `awake`, `hunger_or_weight_below_cap` |
| Origen | Menu Alimentar, ilimitado |

### TONICO / TONIC

Tonico que recupera energia. Conserva el bono antiguo de EV de MP.

Tonic that restores energy and retains its legacy MP EV bonus.

![TONICO](../assets/ui/items/energy.png)

| Campo | Definicion |
|---|---|
| ID | `energy` (indice de interfaz 1) |
| Categoria | Recuperacion |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemEnergy`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | TONICO / TONIC; descripciones arriba |
| Stack maximo | 99 |
| Efecto tipado | `restore`; `ev` |
| Objetivo | `e`, `mp` |
| Magnitud | e +25 (tope 100); mp +2 (tope 252) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `backpack`, `home`, `energy_below_100` |
| Origen | Kit inicial; sin reposicion repetible |

Excepcion legacy: conserva su efecto mixto para no cambiar el balance guardado.

### ESTRELLA / STAR

Insignia de experiencia que aumenta esfuerzo y EV de mente.

Experience badge that increases effort and mind EV.

![ESTRELLA](../assets/ui/items/exp.png)

| Campo | Definicion |
|---|---|
| ID | `exp` (indice de interfaz 2) |
| Categoria | Esfuerzo (legacy) |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemExp`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | ESTRELLA / STAR; descripciones arriba |
| Stack maximo | 99 |
| Efecto tipado | `effort`; `ev` |
| Objetivo | `effort`, `brn` |
| Magnitud | effort +8 (tope 100); brn +2 (tope 252) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `backpack`, `home` |
| Origen | Kit inicial; sin reposicion repetible |

Excepcion legacy: conserva su efecto mixto para no cambiar el balance guardado.

### AMULETO / AMULET

Amuleto generico que mejora el animo; no aumenta fuerza ni evoluciona al pet.

A generic charm that improves mood; it does not increase strength or evolve the pet.

![AMULETO](../assets/ui/items/ring.png)

| Campo | Definicion |
|---|---|
| ID | `ring` (indice de interfaz 3) |
| Categoria | Animo |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemRing`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | AMULETO / AMULET; descripciones arriba |
| Stack maximo | 99 |
| Efecto tipado | `mood` |
| Objetivo | `p` |
| Magnitud | p +15 (tope 100) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `backpack`, `home` |
| Origen | Kit inicial; sin reposicion repetible |

### PROTEINA / PROTEIN

Suplemento alimenticio que recupera energia y aumenta peso, sin EV.

Food supplement that restores energy and increases weight, without EV.

![PROTEINA](../assets/ui/items/protein.png)

| Campo | Definicion |
|---|---|
| ID | `protein` (indice de interfaz 4) |
| Categoria | Alimentacion |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemProtein`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | PROTEINA / PROTEIN; descripciones arriba |
| Stack maximo | Ilimitado en Alimentar; stock antiguo conservado sin uso |
| Efecto tipado | `restore`; `weight` |
| Objetivo | `e`, `weight` |
| Magnitud | e +20 (tope 100); weight +2 (tope 99) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `feeding`, `home`, `awake`, `energy_or_weight_below_cap` |
| Origen | Menu Alimentar, ilimitado |

### BOTIQUIN / MEDKIT

Primeros auxilios: elimina una lesion y recupera salud de cuidado.

First aid: clears an injury and restores care health.

![BOTIQUIN](../assets/ui/items/medkit.png)

| Campo | Definicion |
|---|---|
| ID | `medkit` (indice de interfaz 5) |
| Categoria | Recuperacion |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemMedkit`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | BOTIQUIN / MEDKIT; descripciones arriba |
| Stack maximo | 99 |
| Efecto tipado | `restore`; `heal_injury` |
| Objetivo | `hp`, `injured` |
| Magnitud | hp +20 (tope 100); injured +1 (tope 1) |
| Duracion | Inmediata |
| Limites | `hatched`, `alive`, `backpack`, `home`, `injured` |
| Origen | Kit inicial; sin reposicion repetible |

### GUIA / GUIDE

Manual que da +1 EV en la proxima sesion de atributo completada y guardada.

Manual that grants +1 EV in the next completed and saved attribute session.

![GUIA](../assets/ui/items/guide.png)

| Campo | Definicion |
|---|---|
| ID | `guide` (indice de interfaz 7) |
| Categoria | Mejora de entrenamiento |
| Rareza | Comun, sin tirada aleatoria |
| Icono | `ItemGuide`, sprite RGBA 32x32; runtime 16/20 px |
| ES/EN | GUIA / GUIDE; descripciones arriba |
| Stack maximo | 1 |
| Efecto tipado | `training_ev_bonus` |
| Objetivo | `trained_stat` |
| Magnitud | trained_stat +1 (tope 252) |
| Duracion | Proxima sesion de atributo completada y guardada |
| Limites | `hatched`, `alive`, `backpack`, `home`, `completed_attribute_training`, `keep_on_cancel_or_save_failure`, `keep_if_stat_full` |
| Origen | Jornada completa con buen cuidado (simulador y T-Display) |

## Contratos de uso

- Alimentar contiene solo carne y proteina ilimitadas. No descuenta sus stocks legacy 3/2.
- Carne: +20 hambre y +1 peso; porciones repetidas incluso lleno, hasta hambre 100 y peso 99.
- Proteina: +20 energia y +2 peso; porciones repetidas incluso lleno, hasta energia 100 y peso 99. No da EV ni DP.
- Con peso 99 todavia se recupera hambre/energia; se rechaza sin cambios solo si ambos efectos estan al maximo.
- Amuleto mejora animo, no fuerza. Conserva el ID `ring` y el recurso `ItemRing` por compatibilidad.
- Los cuatro consumibles de mochila se gastan desde casa; la Guia abre entrenamiento y solo se consume al completar la sesion.
- Guia: maximo una; conserva el objeto al cancelar, fallar el guardado o llenar el atributo con el entrenamiento base.
- Los consumibles heredados respetan el limite de stock 99 de la placa. Volver=6 sigue siendo navegacion; Guia=7.
- `hp` del botiquin es salud de cuidado (0..100), no el HP temporal de una pelea. `e` es la energia para entrenar.
- Los EV se limitan a 252 por stat; ningun objeto cambia IV ni la especie.

## Alcance de plataforma

Los siete objetos tienen catalogo y sprite. Los seis legacy y la Guia funcionan en simulador y firmware.
La Guia se guarda en expState y se consume atomicamente con el entrenamiento; no cambia enums guardados.
El inventario muestra tres filas desplazables; no es una bolsa limitada a tres tipos.
Para viajes, topes semanales, cuidado y guardado: [Exploracion](exploration.md).

## Pipeline de arte y validacion

El pixel-art editable vive en `scripts/item_icons.py`; los PNG transparentes exportados estan en `assets/ui/items/`.
`scripts/build.py` genera BMP de pixel nitido y `scripts/build_tdisplay.py` los empaqueta en LittleFS/VPA.
El Amuleto es un colgante de corazon; el Tonico un frasco con rayo; la Guia un libro con marcador.

```sh
.venv-platformio/bin/python scripts/export_item_catalog.py
.venv-platformio/bin/python scripts/export_item_catalog.py --check
make build-tdisplay
```
