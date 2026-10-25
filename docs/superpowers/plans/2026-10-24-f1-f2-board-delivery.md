# Entrega F1/F2 En T-Display

Fecha: 2026-10-24. Solicitud explicita del usuario: commit, push y flash de
la placa conectada. Destino Git: `origin`, `ZIDUK/vpet`, rama `master`.

## Autorizacion Y Alcance

El usuario autoriza esta revision con los ajustes actuales de Status,
conservando la partida y completando despues la validacion fisica pendiente
de sus cuatro paginas. Esta excepcion es solo para esta entrega, no elimina
el gate de Status para cargas futuras.

Incluye ficha evolutiva, definiciones F1, crecimiento F2b y perfil F2a;
Hub local y documentacion acompanante se publican como herramientas host.
El usuario pidio excluir Creator: sus archivos y cambios concurrentes quedan
locales, fuera de esta entrega. El Hub incluido conserva solo catalogo,
vista previa e importacion/validacion local; no incluye rutas de Creator.
No activa WiFi, instalacion USB de paquetes, breeding, roster ni juego P2P.
Los avisos de necesidades siguen sin textos; no se cambia su contrato.

## Checklist

- [x] Verificar destino Git y que master no diverge de origin/master.
- [x] Identificar ESP32-D0WDQ6-V3 y 16 MB por USB.
- [x] Regenerar arte, catalogos y recursos LittleFS (227 assets, 10891653 bytes).
- [x] Pruebas nativas: 185 aprobadas.
- [x] Compilar firmware actual y pasar preflight de memoria.
- [x] Suite Python de la entrega aislada de Creator: 1768 aprobadas en 269.38 s.
- [x] Crear commit de codigo y documentos, sin partidas/backups/logs: `4c6ce16`.
- [x] Respaldo critico NUEVO de tabla de particiones/NVS y checksum local.
- [x] Cargar firmware/LittleFS, verificar hashes y arranque VPET_READY.
- [x] Publicar commit y registro de despliegue en origin/master: `4c6ce16`.
- [ ] Validacion fisica del usuario: cuatro paginas Status, partida,
  entrenamiento, evolucion y reinicio con identidad estable.

## Presupuestos Verificados

Preflight: app 1044313/4194304, assets y manifest 10961760/12451840,
RAM estatica 56228/327680. Los numeros no certifican heap/FPS sostenidos.
No es una garantia de capacidad para cuatro paquetes graficos diferentes.

## Evidencia

Los logs de esta ejecucion se conservan localmente en `/private/tmp/`, con
prefijo `vpet-release-`; los respaldos quedan bajo `out/board-backups/` y
nunca se agregan a Git. Los documentos de
F1/F2 previos describen su verificacion local anterior; este registro anota
por separado la carga efectiva y no convierte compilacion en aceptacion visual.

### Reproduccion Del Commit

La entrega preparada se exporto a un directorio aislado para comprobarla sin
los cambios locales de Creator. Esta comprobacion detecto dos recursos fuente
ignorados necesarios para reconstruir los assets: `assets/ui/fx/bag_sheet.png`
y `assets/ui/fx/grave.png`. Se agregan ambos con excepciones acotadas en
`.gitignore`; no se agregan los directorios de salida ni archivos generados
de PlatformIO. Tras incluirlos, la reconstruccion aislada produjo los mismos
227 assets y 10891653 bytes de payload, y las 26 pruebas de Hub/pipeline pasaron.
La suite completa sobre este arbol aislado termino con 1768 pruebas aprobadas
en 269.38 s y 13239 advertencias existentes. Esta evidencia no certifica
los cambios concurrentes de Creator, que no forman parte de ese arbol.

### Respaldo Y Carga

Respaldo nuevo en `out/board-backups/release-20261024-101443/`: 24576 bytes
de tabla de particiones y NVS, con SHA-256 comprobado. Se escribieron app y
LittleFS; no se borro ni restauro NVS. La conservacion visual de mascota y
progreso requiere todavia la confirmacion del usuario.

La primera carga de firmware termino, pero el subprocess de `uploadfs`
fallo con `RuntimeError` y `lost sys.stderr`. El reintento directo de
PlatformIO `-t uploadfs` termino correctamente. Despues, una verificacion
independiente con `esptool verify_flash` confirmo ambos digests en la placa:

- App en `0x10000`, SHA-256
  `66f9dc1e408d5271391d360a5d193a440710290dcc3e48c5ce8b7a34412c8d41`.
- LittleFS en `0x410000`, SHA-256
  `da048520cb1cecae0d63993ccbfd4f775acb6fca795da3da05e3f00e9d80cf82`.

### Arranque Y Limites De La Observacion

`VPET_READY` confirmado, manifest `1`, flash 16777216 bytes, filesystem
11804672/12451840 bytes y heap libre de arranque 65968 bytes. La observacion
serial posterior de 70 segundos registro BLE conectado, heap libre estable
en 65964 bytes y minimo 60768 bytes, sin otro reinicio tras el arranque inicial.
Esto no certifica sesiones largas, fluidez visual ni ciclos de reconexion BLE.
La aceptacion fisica de Status sigue pendiente y se solicito al usuario.

### Publicacion

`4c6ce16` (`feat: deliver portable pet definitions, DNA growth and profiles`)
publicado en `https://github.com/ZIDUK/vpet.git`, rama `master`.
La confirmacion del push registra el avance `f733c60..4c6ce16`.
Este cierre documental posterior no cambia firmware ni requiere otro flash.
Los cambios locales de Creator permanecen sin publicar y sin revertir.
