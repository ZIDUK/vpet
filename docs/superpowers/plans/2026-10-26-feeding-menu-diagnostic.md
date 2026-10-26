# Alimentacion Permanece En FEED: Diagnostico

Fecha: 2026-10-26. Estado: abierto; pendiente de valores reales de cuidado.

## Evidencia Del Usuario

IMG_4260 muestra dos individuos y dos plazas libres. El usuario confirma,
tras el recorrido solicitado, conservacion al guardar/reiniciar y stats
individuales con stock compartido al cambiar de mascota. No se infiere
aceptacion de incubacion o breeding a partir de esa confirmacion.

IMG_4262 muestra FEED con MEAT seleccionado. El usuario precisa que ACTION
permanece en el selector en vez de mostrar la animacion. No ha confirmado
si cambia la saciedad. Se pide foto del cuidado y estado actual de Pause Pet;
no se despausa, alimenta ni modifica la partida por el usuario.

## Flujo Inspeccionado

App::handlePanelInput aplica Nutrition::applyFood sobre el estado activo.
Solo Applied mas commit correcto inicia Motion::startAction(Feed) y Home.
Un rechazo conserva el panel. La carne rechaza con saciedad 100 y marca de
sobrealimentacion del ciclo; proteina rechaza tras su toma del ciclo o si
no cabe el aumento de energia. Tambien se rechazan huevo, muerte, pausa y
sueno. No se relajan esas reglas para mostrar una animacion de consumo.

Panels::drawFeeding dibuja UNLIMITED para carne incluso cuando el ciclo no
permite otra toma; el indicador de proteina solo explica su propio reposo.
Es un limite de claridad confirmado en codigo, no prueba del motivo exacto
en la mascota de la foto. Un fallo de guardado sigue siendo una alternativa
que requiere evidencia; no se presenta como reproducido.

## Comprobacion Host

tests/collection_app.cpp ejercita ocho combinaciones del App real con
CollectionStore sintetico: Firemon/Flamemon y carne aceptada, proteina
aceptada, carne rechazada por saciedad/ciclo, carne rechazada por pausa.
Comprueba estado Eat, fotogramas, efecto persistido unico y retorno desde
Eat; los rechazos conservan panel, cuerpo y almacenamiento. No escribe NVS
legacy ni usa datos reales. El renderer de prueba observa MotionState;
no dibuja assets ni certifica la animacion visible en el TFT.

La prueba focalizada pasa sin cambiar produccion: 1 aprobada en 5.57 s.
Esto caracteriza el comportamiento actual, no es una reproduccion RED de
un defecto ni una correccion cargada. No se vuelve a flashear ni se cambian
los limites de comida. La validacion del motivo real sigue abierta.

Verificacion ampliada: 89 pruebas focalizadas aprobadas en 36.54 s, con
150 advertencias existentes de Pillow. Incluye los siete consumidores del
renderer de prueba ampliado. git diff --check sin errores. No se ejecuta una
suite completa ni un build nuevo porque solo cambian pruebas y documentos.
