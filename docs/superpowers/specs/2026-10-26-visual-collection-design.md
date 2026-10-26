# Coleccion Visual

El usuario pide reemplazar el menu textual por imagenes y seleccion visible
de dos padres, y solicita continuar. La pantalla fisica actual muestra
"Migrar": la coleccion aun no fue activada. No ejecutar esa operacion en su nombre.

## Alcance

- Cuatro plazas visibles en una cuadricula 2x2, con retrato, nombre, sexo y
  marca de activo; plazas libres con marcador grafico. Comandos huevo, cruce,
  volver separados de los individuos, con iconos existentes.
- Ficha con retrato grande, nombre y estado; quitar el ID hexadecimal de la
  vista principal. Activar, elegir padre, preferencias y volver son acciones
  independientes. Preferencias en placa usan solo la politica activa ya cargada;
  un individuo inactivo muestra que se necesita activarlo, sin reservar otra politica.
- Cruce en dos pasos: fijar primer padre y seleccionar pareja, retratos grandes
  enfrentados y miniaturas de candidatos. Mostrar solo candidatos elegibles como
  seleccionables; volver siempre disponible. Confirmacion separada y cancelacion
  predeterminada. El huevo es ilustrativo, sin adelantar especie, sexo o ADN.
- Bienvenida con la mascota actual y "Activar coleccion", no jerga de migracion.
  Una segunda confirmacion preserva el consentimiento anterior.
- Confirmaciones visuales de huevo fundador, cambio y cruce. No conceder efectos
  al navegar, dibujar, cancelar o generar las galerias.

## Restricciones

240x135, dos botones, recursos existentes y sin otro framebuffer permanente.
No cambiar Status, ADN, elegibilidad, tiempo, limites, guardado ni enums existentes.
ES/EN; nombres largos dentro de su region. No inventar progreso de aprendizaje.
Mantener Creator concurrente fuera del alcance. Esta tarea valida localmente;
carga, publicacion y aceptacion de placa se reportan por separado.
