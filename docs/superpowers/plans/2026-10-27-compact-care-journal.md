# Compact Care Journal Implementation

**Approved:** The user approved compact transactional care persistence after the
board measured 4.2-7 second saves with frozen animation. No new flash is approved.

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
warnings. No board deployment occurred. The prepared artifact is not physical
acceptance; the last on-board fluency result remains failed.

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
