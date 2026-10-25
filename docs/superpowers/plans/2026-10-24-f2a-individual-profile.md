# F2a: Individual Profile

## Scope

Implement identity, sex and known parents in simulator and active ESP32 firmware.
No UI/Status, breeding, collection, protocol, radio, balance or hardware deployment.

## Decisions

- Portable `PetProfile`: canonical `1:<32 lowercase hex>:M|F:<parent|->:<parent|->`.
  Four random 32-bit words identify an individual; the first word's low bit
  selects M/F (50/50 for uniform input), independently of DNA and combat.
  Reject all-zero IDs, malformed/future records, duplicate/self parents and
  partial parent pairs. Founders have two unknown parents, not invented lineage.
- Domain objects can be unassigned for isolated previews/tests. Production
  persistence injects entropy: OS random bytes in simulator, ESP32 random source
  in firmware. IDs are probabilistic identifiers, not authentication tokens.
- New life clears the profile; hatching/evolution retain it. Load old saves
  through existing persistence and durably add the profile before play; do not
  reroll DNA, EV, sleep, rewards or inventory as a profile migration effect.
- Keep NVS schema 3/enums unchanged. Add `petProfile` string and snapshot v5
  only for assigned profiles; decode historical v1-v4 journals without erasing
  an additive profile. Include profile in primary/reserve swap intents.
- A rejected write does not publish the candidate identity. Accepted pending
  intent retains it for idempotent recovery; gameplay waits for storage recovery.
  Reserve migration is lazy on swap. No promise of uniqueness after cloning an
  identified save: a backup is the same individual, not a new pet.
- Sex is stored from the egg, with no new on-screen reveal in this phase.
  Parent references reserve the contract only; no offspring creation or
  ancestry eligibility algorithm is enabled.

## Checklist

- [x] Failing tests: codec, lifecycle, migration, errors, cross-language parity.
- [x] Portable Python/C++ profile, platform entropy and persistence integration.
- [x] Primary/reserve and interrupted writes; historical journals preserved.
- [x] Full Python, native core and ESP32 build (no flash).
- [x] Architecture, roadmap, product and launch documentation updated.

## Focused Evidence

12 dedicated Python tests include real C++ profile/storage binaries and
1024 matching serialized profiles, lifecycle/parent rejection, rollback,
legacy `life=0`, migration/swap cutpoints and the platform entropy lifecycle.
Four additional `profile_*` cases exercise the actual NVS adapter's Pending
semantics using its driver stub. With the existing adapter matrix: 52 passed.
Two simulator route tests retain their strict one-gameplay-commit assertions;
startup persistence has its own test and no longer pollutes that counter.

The adopted-items generator now emits the F2b wide-stat documentation already
present in its generated Markdown; `--check` passes without changing item
definitions, sprites or rewards. Previous failed full runs remain diagnostic
history, not delivery evidence. Only their own completed temporary directories
were removed for disk space; no save or board backup was removed.

## Final Verification

- Frozen-source full suite: 1768 passed, 13239 existing warnings, 286.54 s.
- PlatformIO native: 185 passed, 1.40 s.
- ESP32 build: success, 8.89 s; RAM 56228/327680, app 1044313/4194304.
- Both content/adopted generators `--check`, `git diff --check` and 200
  local links across 11 documents passed.
- Logs, machine-readable results and 19 source hashes retained in
  `out/individual-profile/`; hashes rechecked after the full run.
- No new assets, WiFi, hardware access, deployment, commit or push.

Physical acceptance, a sex display, roster and breeding remain open.
