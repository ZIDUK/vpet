# SPEC-GAME-FOOD-001: Porciones Repetidas Y Aumento De Peso

## Estado Y Aprobacion

Estado: approved, 2026-10-29. El usuario solicito repetir proteina y
carne para aumentar peso y aprobo expresamente: "Si, incluso estando lleno".
El usuario aprobo este documento: "Si, implementar esta especificacion".
La implementacion requiere plan separado y registro REQ/AC en
docs/requirements.json. No se atribuye aprobacion retrospectiva al balance viejo.

## Problema

Actualmente se bloquea la segunda proteina del ciclo metabolico y se permite
una sola carne extra con saciedad 100. Estos candados impiden repetir porciones
para recuperar energia o aumentar peso como espera el usuario.

## Objetivo

Permitir porciones repetidas, incluso estando lleno, sin sobrepasar los topes
actuales ni conceder EV por comer.

## Alcance

Reglas portables C++ del T-Display y Python del simulador, preview, catalogo
de efectos/condiciones y documentacion generada. Se conserva Alimentar con
solo dos alimentos ilimitados, sin consumir existencias legacy de Mochila.

## Exclusiones

Sin cambios de ADN, etapas, balance de combate, muerte, sueno, metabolismo,
entrenamiento, penalizaciones por peso, Hub, layout Status o transporte USB.
No se concede energia directamente ni se agregan comandos de prueba a la placa.

## Requisitos

### REQ-GAME-FOOD-001

Carne puede repetirse sin esperar ciclo: cada porcion aceptada aplica
min(100, saciedad + 20) y min(99, peso + 1), incluso con saciedad 100.
Proteina puede repetirse sin esperar ciclo: aplica min(100, energia + 20) y
min(99, peso + 2), incluso con energia 100 o entre 81 y 99.

### REQ-GAME-FOOD-002

Rechazar sin mutacion cuando ambos efectos del alimento estan ya al maximo:
carne con saciedad 100 y peso 99; proteina con energia 100 y peso 99. Peso 99
no impide recuperar saciedad/energia faltante. Mantener las restricciones de
huevo, muerte, pausa, sueno y accion ocupada. No sumar EV, esfuerzo ni DP.

### REQ-GAME-FOOD-003

Preview y aplicacion coinciden. Cada confirmacion aplica una sola porcion y
conserva el escritor en segundo plano y las garantias de recuperacion ante
rechazo/reinicio. Catalogo y docs ya no anuncian limites por ciclo.

## Criterios De Aceptacion

### AC-GAME-FOOD-001

Con energia 0 y peso 10, seis proteinas consecutivas dejan energia 100 y peso
22. Con saciedad 100 y peso 10, tres carnes dejan saciedad 100 y peso 13.
Los flags historicos de ciclo no bloquean estos usos. No cambia ningun EV.

### AC-GAME-FOOD-002

Con peso 98 y energia 95, proteina deja peso 99 y energia 100; repetir se
rechaza sin cambiar contadores. Con peso 99 y energia 60, dos proteinas son
validas y dejan energia 100 y peso 99. Aplicar casos equivalentes para carne.
Huevos, muertos, dormidos, pausados y ocupados siguen rechazando la comida.

### AC-GAME-FOOD-003

Firmware y simulador producen los mismos resultados, sin consumir stock ni
ganar EV. Guardar/cargar conserva efectos y acepta datos anteriores con flags
de ciclo activos. Un rechazo de persistencia no concede otra porcion ni cambia
el estado durable. Una pulsacion repetida durante guardado se ordena una vez.

## Contratos Y Compatibilidad

Conservar firmas applyFood, food_preview y apply_food, numeric enums, NVS
schema y datos anteriores. Los flags historicos de ciclo permanecen legibles,
pero dejan de ser candados. Se mantienen contadores historicos de comidas y
excesos con sus topes actuales. El rechazo sin efecto usa Full/full, sin
renumerar FoodResult ni inventar una migracion destructiva.

## Errores Y Recuperacion

Reutilizar el commit compacto y rollback existentes. No editar partidas,
reformatear LittleFS, agregar guardado completo sincrono o mostrar GUARDANDO.
Mantener disponibilidad/cancelacion y una animacion de comer por uso aceptado.

## Riesgos

Recuperar energia repetidamente facilita entrenar; es un cambio de balance
pedido por el usuario, no una validacion de equilibrio. El peso adicional
conserva las penalizaciones existentes por condicion corporal. No confundir la
confirmacion del usuario de un entrenamiento sin congelarse con aceptacion de
todos los recorridos de persistencia invisible.

## Verificacion

Antes de implementar, pruebas rojas de porciones repetidas en Python y C++.
Despues: limites, preview/aplicacion, compatibilidad y rollback; regenerar el
catalogo desde fuente; make spec-check, pytest tests/, native y build tdisplay.
La comprobacion fisica de comida repetida solo se registra despues de una carga
autorizada y observacion real. Este documento no afirma pruebas ni despliegue.

## Preguntas Pendientes

Sin decisiones de producto abiertas. Documento aprobado para implementar.
