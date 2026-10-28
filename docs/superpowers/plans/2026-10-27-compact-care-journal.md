# Compact Care Journal Implementation

**Approved:** The user approved compact transactional care persistence after the
board measured 4.2-7 second saves with frozen animation. Implementation approval
did not include flashing; separate flash approval was received on 2026-10-28.

**Design:** An optional portable CareJournal stores one bounded absolute active
snapshot in the existing NVS namespace. It binds base Collection generation,
active slot and identity, elapsed collection time and monotonic journal revision
with CRC. One atomic key replacement is the care commit point; Pending is not
reported settled. No unbounded queue or volatile-only care success.

The Collection base file remains VPCL v1. Loading validates that file first,
then overlays a matching journal. Future/foreign/corrupt records block recovery;
records from an older already-checkpointed generation are ignored, not replayed.
Structural checkpoints merge the active body and shared stock before publishing
the new generation; a leftover old journal is safe if power fails before cleanup.
Existing legacy journals remain readable. The compact path targets enabled
Collection; legacy full snapshots keep their current fallback behavior.

## Steps

1. RED tests: care does not commit a Collection generation, reboot restores exact
   state, repeated care overwrites one record, failures/recovery never duplicate
   effects, stale writers/foreign identity/future/corrupt data fail closed.
2. Implement bounded codec, explicit NVS missing/error reads, atomic write/sync
   and readback. Limit the record below NVS's 4000-byte string bound; preserve
   all existing keys and fail closed on capacity errors in the 20 KiB partition.
3. Overlay care in CollectionStore load/read, use cheap base-header/CAS guards
   for care writes and merge pending state for every structural checkpoint.
   Persist powered-on cooldown/incubation without rewriting the full collection.
4. Wire CollectionPanel/App care jobs, recovery and main.cpp journal injection.
   Keep Creator changes unstaged. Test real App meals/items/lights plus switching,
   structural commits, learning, incubation and fault boundaries.
5. Run focused/full isolated tests, native suite and isolated firmware build,
   request independent review and update architecture/status. Ask for separate
   flash approval only after validation. Hardware latency remains unverified.

## Compatibility And Safety

No assets, Status layout, numeric enums, WiFi or partition changes. A compact
journal is additive persistence: downgrading to firmware without support requires
a successful full checkpoint first. Never restore a pre-test backup over new
user progress. An interrupted or out-of-space commit cannot credit a new action.

## Verification Evidence

The initial compact regression failed because care still committed a complete
Collection generation. It now checks zero Collection commits for repeated care,
exact reboot state, shared stock, stale structural writers, foreign identity,
future/corrupt/truncated records, and every filesystem failure point during a
structural merge. Separate checks exercise cumulative incubation/cooldown,
evolution checkpoints, and old/new durable outcomes of an uncertain NVS commit.

The actual App harness covers food, items, sleep/wake, consecutive meals,
Rejected/Pending recovery and minute checkpoints. Independent review found a
stale-writer hole and lost care time at failed timer checkpoints; regressions
cover both. The latter reproduced RED before the deferred-pet-time fix. The
final static re-review reports no unresolved finding, not physical acceptance.

Focused tests: 57 passed in 16.45 s. Native tests: 185 passed in 2.970 s.
Firmware build: 7.768 s, static RAM 53404 bytes, app 1114965 bytes, binary
1121536 bytes. SHA-256:
`ce2734a17a52599679d48ae18a2fb1e010a8575fa71ff5505f180851acdf4cfc`.
Build and full-suite workspace exclude Creator; owned source/test checksums
match that isolated workspace. Artifacts: `out/compact-care/`.
Full isolated suite: 2027 passed in 310.10 s, with existing deprecation/palette
warnings. No board deployment had occurred at that local-validation stage.
The prepared artifact is not physical acceptance; see the subsequent load below.

## Next Physical Gate

After separate flash approval, take a fresh backup without restoring an old
save, flash firmware only, and verify app/unchanged NVS/LittleFS digests. With
Pause Pet OFF, the user tests eligible MEAT twice, an effective item once and
lights off/on. Capture first-draw/save durations, loop maximum, heap and worker
stack; require animation without the previously reported freeze. Then reboot
only after settled confirmation and check exact food/stock/sleep state without
first forcing a manual full save, which would hide a journal-recovery defect.
Do not automate consumptions or create/switch/breed pets for this gate. BLE,
long sessions and full structural workflows remain separate acceptance checks.

## Deployment: 2026-10-28

The user explicitly approved loading and measuring. Recreated the isolated
workspace from git archive ce68348 after the temporary workspace disappeared;
Creator remains excluded. Clean build 16.818 s, preflash build 3.633 s, focused
57 tests passed in 16.10 s. Static RAM/app/bin sizes are unchanged. Only the
embedded ELF hash and trailing image hash differ from the original binary.
Loaded SHA-256:
`ad31882cb3e863d6b2d1dc2197c56b7a07e26eee98989a38a0c8737e16bab153`.

The first backup attempt at 921600 failed before any flash write. The retry at
115200 created a fresh verified backup in
`out/board-backups/compact-care-20261028-080406/`. LittleFS was reconstructed from
a verified baseline plus 11 device-read changed blocks, then matched against
the current full-device filesystem digest. No old save was restored. Only app
0x10000/1121536 bytes was written; app and unchanged boot/partition/NVS/LittleFS
digests were verified before reset. READY: heap free 80692, minimum 71160,
16 MiB flash, manifest 1.

The script exited nonzero after verified boot because the real LittleFS usage
leaves 622592 bytes/5% free, below the 10% storage margin. The previous firmware
reported exactly the same 11829248/12451840 usage. This is not a new allocation
or a failed app write; it remains an unresolved capacity gate, not waived or
fixed by deleting files. Backup verification.json retains this diagnostic.

Read-only capture `out/compact-care/capture-20261028-080817.json`: 20.099 s,
zero sent commands/inputs, one startup sequence observed on opening USB, one
runtime sample, no fatal lines, heap free 80248/minimum 71160, loop maximum
524853 us, BLE=0. This does not establish sustained liveness, action latency,
radio behavior or visual fluency. User-driven care tests remain pending.
