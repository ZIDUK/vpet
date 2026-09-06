# Compact Evolution Tree Design

## Goal

Replace the fixed three-card evolution guide with a compact, branch-aware tree
that remains inside the 128x112 playfield below the menu. Known forms show their
real portrait. Undiscovered forms remain black silhouettes labeled `???` until
the pet reaches that form for the first time.

The physical display remains 128x128. Visual quality improves through tighter
source cropping, nearest-neighbor scaling, controlled portrait sizes and a
large detail view rather than by claiming additional hardware resolution.

## Interaction

The guide has two modes: `tree` and `detail`.

- Opening the book starts in `tree` mode with the current species selected.
- NEXT moves through visible nodes from left to right. Within branches at the
  same stage, traversal proceeds from top to bottom before continuing.
- Traversal wraps after a final `BACK` node.
- ACTION on a species opens `detail` mode.
- ACTION in `detail` returns to the tree without changing the selected node.
- ACTION on `BACK` closes the guide.
- Undiscovered nodes can be selected, but their detail view shows only the
  silhouette, stage and `???`; it does not expose their name or requirements.

## Tree Layout

The panel reserves four physical pixels at every outer edge. It displays a
three-stage horizontal window: predecessor, selected stage and next stage.
Straight relationships use a single connector. A stage with multiple possible
forms uses a split connector and vertically stacked nodes.

At most two branch nodes are drawn simultaneously in one column. When a stage
has more branches, NEXT scrolls the selected branch into view and the panel
draws small up/down continuation indicators. No card or portrait may cross the
panel bounds.

Overview portraits fit within 24x24 pixel boxes after transparent-border
trimming. The selected node uses a yellow border; discovered nodes use the
normal dark frame; silhouettes use solid black artwork on the parchment fill.

## Detail Layout

The detail view dedicates up to 64x64 pixels to one pet and uses the first idle
frame from its existing atlas. This avoids another large runtime asset and
preserves more detail than the overview thumbnail.

Discovered forms show their name and stage. The current form is labeled
`CURRENT`. A discovered future or sibling form may show requirements only when
real rules exist in the evolution catalog. Missing gameplay rules are presented
as `REQUIREMENTS NOT DEFINED`; no thresholds are invented.

## Evolution Graph

Evolution data becomes graph-compatible while accepting the current single
string format during migration. Each species can expose zero, one or multiple
next species. Rendering derives stage columns and connectors from this catalog
instead of hard-coded Firemon, Flamemon and Dragfiremon coordinates.

The current line remains:

```text
Firemon -> Flamemon -> Dragfiremon
```

No fictional sibling evolution is added. When another Ultimate is registered
as a possible Flamemon result, the tree automatically adds a second Ultimate
node. It remains `???` until reached.

## Discovery Persistence

`Pet` stores a unique list of discovered species in `pet_save.json`.

- A new pet begins with its current species discovered.
- Successful evolution records the resulting species immediately.
- Loading an older save without discovery history seeds the list with its
  current species, preserving backward compatibility.
- Resetting the simulator creates a new discovery history.
- Merely satisfying requirements, viewing a silhouette or force-previewing the
  guide does not reveal a species.
- Simulator key `e` performs a real registered evolution and therefore reveals
  the resulting species.

## Rendering And Build

`scripts/build.py` generates tightly cropped 24x24 overview portraits and
matching silhouette BMPs for every registered form that has artwork. The
simulator and CircuitPython runtime consume the same generated files and layout
constants.

The detail view reuses existing 64x64 idle atlases. All scaling uses nearest
neighbor sampling and transparent palette index zero. Build validation rejects
missing portraits, invalid graph targets and generated art that exceeds its
declared dimensions.

## Failure Handling

- A graph target without species data fails the build with the missing ID.
- A registered species without portrait artwork renders a silhouette and logs
  a build warning only when that species is intentionally undiscovered.
- Invalid or duplicate discovery entries are ignored during save loading.
- An unknown current species falls back to one centered `???` node without
  crashing the simulator or board runtime.

## Tests

Tests cover graph traversal, branching, discovery migration and persistence,
reveal-on-evolution, hidden names, cursor wrapping, branch scrolling and BACK.
Pixel tests verify four-pixel margins, portrait bounds, silhouette rendering,
selection borders and the 64x64 detail frame. Pipeline tests verify generated
portrait dimensions and simulator/board asset parity. The final check runs the
complete test suite plus a headless simulator render.

## Out Of Scope

This change does not choose Flamemon-to-Dragfiremon automatic requirements, add
a sibling evolution, increase the physical LCD resolution or deploy to the
board. Those gameplay and deployment decisions remain separate work.
