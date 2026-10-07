# Estado y alcance del proyecto

Actualizado el 2026-10-06. El arbol contiene cambios locales posteriores a
`3b98843`; ese hash no representa todo el estado actual.

## Confirmado

- El telefono detecta el vPet por BLE cuando el modo `ADVERTISING` esta activo.
- WiFi esta deshabilitado y no aparece en el menu del dispositivo.
- La navegacion de dos botones y las animaciones tienen una respuesta mas
  fluida que las versiones anteriores.
- El simulador y el firmware comparten recursos y reglas principales.
- La intro de arranque existe en ambos entornos, pero aun no se ha cargado a la
  placa despues del ultimo commit.
- `make sim-practice` y el icono de espadas abren directamente el combate
  determinista. `make sim-training` abre entrenamiento y tecnicas en la pesa.
  Ambos comandos comparten un guardado de preview separado de la partida normal.
- En el simulador Firemon tiene seis entrenamientos por atributo con iconos,
  coste de 8 ENE, ganancia de 6 EV y vista antes/despues. No cambia sus IV.
  Aprendizaje y dominio de tecnicas se abren desde la pesa; Guardia usa `block`.
- El motor de practica Python/C++ tiene trazas comparadas y pruebas nativas;
  la vista y persistencia NVS estan integradas en codigo y compiladas, sin
  despliegue ni validacion fisica del flujo nuevo.

## Pendiente de producto

- Definir el contenido descargable: pets, themes, bundles, metadata, licencias
  y limites de almacenamiento.
- Definir los nuevos pets, sus sprites, acciones, estadisticas y evoluciones.
- Implementar el esquema publico `.vpetpack` y su validador.
- Implementar el catalogo web y sus previews.
- Implementar instalacion inicial por USB/Web Serial.
- Implementar posteriormente aprovisionamiento WiFi y descargas HTTPS.
- Diseñar una app movil para estado, BLE y gestion de contenido.

## Pendiente tecnico

- Trasladar a C++ el entrenamiento por atributo y la nueva interfaz de
  pesa/tecnicas/combate con iconos. El firmware conserva el flujo anterior;
  la paridad del motor de combate no implica paridad de estas nuevas pantallas.
- Ajustar con pruebas de juego los costes y ganancias de entrenamiento.
- Conectar feedback de impacto con `hit`/`hurt` ya disponibles. `dodge` tambien
  existe, pero no se usa para insinuar una evasion que el motor aun no calcula.
  Sprites sugeridos nuevos: victoria, derrota y ejercicios especificos.
- Igualar la intro: firmware usa un sprite Firemon fijo; simulador muestra
  texto FIREMON. Aun no usa la mascota guardada. La intro bloquea el arranque
  durante aproximadamente 2.2 segundos y no tiene pruebas dedicadas.
- Corregir divergencia de eclosion: App.cpp y config.py usan 2 segundos;
  el catalogo generado declara 8 segundos. La documentacion anterior decia 8.
- Revisar paridad de Status/DNA, descanso y guardado entre Python y C++.
  Son implementaciones separadas, aunque comparten recursos generados.

- Probar en la placa la intro posterior al commit.
- Confirmar el ciclo BLE `ADVERTISING -> CONNECTED -> ADVERTISING` desde el
  telefono y dejar evidencia serial.
- Añadir pruebas de regresion para la intro y los nuevos paquetes cuando se
  defina el contrato.
- Validar practica en pantalla y botones reales, restauracion NVS y BLE activo
  cuando se autorice el despliegue.
- Separar una configuracion de firmware de produccion con Secure Boot, Flash
  Encryption, OTA firmada y anti-rollback.

La board actual se mantiene como dispositivo de desarrollo. Ningun cambio se
considera validado fisicamente hasta que se cargue de forma explicita y se
pruebe en pantalla, botones y radio.
