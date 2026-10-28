# vPet Creator Implementation Plan

Spec separada: [SPEC-HUB-CREATOR-001](../specs/2026-10-28-vpet-creator-design.md).
Es una reconstruccion pendiente de revision, no una aprobacion retroactiva.
Este archivo conserva pasos/evidencia historicos, no define un nuevo contrato.

Trazabilidad del piloto:
- REQ-HUB-CRT-001: generacion y reapertura del ZIP.
- REQ-HUB-CRT-002: cuadriculas, limites y aliases.
- REQ-HUB-CRT-003: bloqueo por recursos ausentes.
- REQ-HUB-CRT-004: PNG, dimensiones y presupuesto.
- REQ-HUB-CRT-005: ausencia de mutacion y ADN.
- REQ-HUB-CRT-006: creditos/layouts fuente.
- REQ-HUB-CRT-007: recorrido navegador y borradores.
- REQ-HUB-CRT-008: importacion de metadatos sin instalacion.

Goal: implement the approved local authoring assistant, without a store or board writes.
Architecture: browser form/preview plus host-side PNG validation and F1 generation.
Export is an authoring ZIP, not a signed installable vpetpack. Existing core rules stay intact.

- [x] Test generated definitions, PNG grids, aliases, missing files and malicious/oversized inputs.
- [x] Implement scripts/hub_creator.py: inspect_project(document) and export_project(document).
- [x] Add bounded same-origin POST endpoints /api/creator/check and /api/creator/export.
- [x] Add four-step UI, live PNG grid preview, generated JSON, draft save/load and ZIP download.
- [x] Check the actual exported ZIP using F1 validation, then browser desktop/mobile flows.
- [x] Document authoring format, limits and missing publication/install steps.

Evidence: 19 creator tests plus 8 Hub tests pass. Previous focused run also
included 34 F1 tests, passing. Chromium complete flow at 1280/390px passes,
including downloads, draft restoration, incomplete project blocking, nonblank
canvas and no JS errors/overflow. Actual browser ZIP: 30 unique safe paths,
content.json accepted by PetDefinition and prepared art accepted by validate_art.
Existing catalog/import browser regression also passes. Screenshots inspected
in out/creator-animation-desktop.png and creator-review-390.png.

Full suite attempted but not certified: ENOSPC on the Mac caused widespread
temporary-file failures (disk reported 115 MiB free). Removed only pytest-8
temporary output created by this execution; no backups/user data were touched.
No firmware/core edit, board connection, flash, publication or push.

Limits: 24 MiB HTTP body, 16 MiB decoded PNG total, 4 MiB per PNG,
4096px per dimension, 8 megapixels per source, 1..64 frames, square cells up to 512px.
Prepared atlases use 88px cells and index-zero transparency; portraits use 40px,
backgrounds use 240x135. No external ZIP extraction or arbitrary path writes.
Identity/credits live in project.json, separately from the strict internal F1 content.json.
Drafts are explicitly downloaded/reopened by the user, not silently persisted on the server.
