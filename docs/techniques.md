# Tecnicas y espacios por evolucion

Contrato vigente desde 2026-10-18, aprobado para Python y T-Display.
Sustituye el limite de dos y el catalogo inicial de tres de la referencia
historica `superpowers/specs/2026-10-14-technique-standard.md`.

| Etapa | Espacios equipables | Catalogo accesible |
| --- | ---: | --- |
| Firemon | 2 | Golpe, Llama, Guardia |
| Flamemon | 3 | Anteriores y Rafaga |
| Dragfiremon | 4 | Anteriores e Inferno |

| ID / indice estable | ES / EN | Elemento | Poder | MP | Alcance | Recarga | Requisito |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| punch / 0 | GOLPE / PUNCH | neutral | 12 | 0 | 1 | 0 | Innata |
| flame / 1 | LLAMA / FLAME | fire | 24 | 8 | 2 | 1 | 2 lecciones |
| guard / 2 | GUARDIA / GUARD | ninguno | 0 | 0 | 2 | 0 | Innata |
| flare / 3 | RAFAGA / FLARE | fire | 30 | 12 | 2 | 1 | Flamemon+, 4 lecciones |
| inferno / 4 | INFERNO / INFERNO | fire | 38 | 18 | 2 | 2 | Dragfiremon, 6 lecciones |

Lecciones significa el contador acumulado `training` de Tecnicas, no EV ni
sesiones de atributos. Cada leccion cuesta 4 energia, suma 1 al contador y
1 al vinculo; si la tecnica elegida ya cumple el umbral despues de la leccion,
suma 5 de dominio, hasta 100. No se entrena una tecnica de etapa futura.
Noche conserva su contrato: ensena Llama hasta dos, despues mejora su dominio;
no ensena Rafaga/Inferno directamente ni equipa nada.

Aprender y equipar son acciones distintas. Evolucionar conserva el equipo y
dominio; los espacios nuevos quedan vacios. Equipar con todos ocupados
sustituye la tecnica de mayor indice, como en el comportamiento anterior.
No se puede quitar la ultima equipada. Reiniciar vida restablece el progreso.

Golpe/Guardia/Llama mantienen poder, MP y recarga. Las nuevas usan la misma
formula, la ventaja elemental x3/2 antes de Guardia y minimo 1. La recarga
bloquea las siguientes 1/2 decisiones de ronda; AUTO/ordenes no permiten MP
negativo. El alcance es metadato: Arena no incorpora posiciones tacticas.
No hay efectos de estado ni firmas. Rafaga/Inferno usan el cast propio de la
etapa y cada una tiene un icono pixel-art generado distinto.

## Persistencia

No cambia el schema NVS 3 ni los valores de SpeciesId. Se conservan techVer 1,
techTrain, techBond, techM0..2 y los bits 0..2 de techEquip. Se agregan techM3/4
con cero por defecto y bits 3/4; la carga filtra equipo por etapa/aprendizaje.
El registro transaccional saveTx/swapLive/swapBack se escribe como snapshot
interno v3 y lee v1/v2/v3; los antiguos no tenian los campos adicionales.
itemTx mantiene sus campos y admite techEquip hasta 31. El estado completo
se recupera una sola vez, incluso tras interrupciones de escritura.

El JSON del simulador mantiene version 1 y IDs de texto: agrega dominio para
flare/inferno, acepta documentos antiguos y conserva cuatro equipadas de la
etapa correspondiente. Si guardar entrenamiento/equipo falla, revierte la
mutacion. No se promete que un firmware antiguo pueda leer progreso ampliado.

## Validacion

`tests/test_technique_expansion.py`: etapas, coste/recarga, aprendizaje manual,
rollback, migracion y 48 trazas completas Python/C++ con fuego/planta/agua.
`tests/test_training_pixel_parity.py`: raster real C++ contra Python, ES/EN,
cinco tecnicas, seis selectores y equipo de 2/3/4.
`tests/test_persistence_atomic.py`: interrupciones en save/swap/park y recuperacion
con los nuevos dominios/equipo. La prueba host no sustituye aceptacion fisica.
