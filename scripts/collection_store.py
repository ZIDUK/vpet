"""Checksummed two-generation collection storage; never touches legacy saves."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from core.collection import Collection, MAX_BYTES, unique_object


class CollectionCommitUncertain(OSError):
    """Rename is visible but directory durability failed: reload before writing."""


class CollectionRepository:
    def __init__(self, root):
        self.root = Path(root)

    def _records(self):
        result = []
        present = False
        invalid = False
        for index in range(2):
            path = self.root / ("generation-%d.json" % index)
            try:
                with path.open("rb") as stream:
                    raw = stream.read(MAX_BYTES + 1025)
            except FileNotFoundError:
                continue
            present = True
            if len(raw) > MAX_BYTES + 1024:
                invalid = True
                continue
            try:
                wrapper = json.loads(raw, object_pairs_hook=unique_object)
                if type(wrapper.get("version")) is not int or wrapper["version"] != 1:
                    raise RuntimeError("Unsupported collection generation")
                sequence = wrapper["generation"]
                if type(sequence) is not int or not 1 <= sequence <= 0xFFFFFFFF:
                    invalid = True
                    continue
                if set(wrapper) != {"version", "generation", "payload", "sha256"} or sequence % 2 != index:
                    invalid = True
                    continue
                payload = json.dumps(wrapper["payload"], separators=(",", ":"), sort_keys=True, allow_nan=False)
                if hashlib.sha256(payload.encode()).hexdigest() != wrapper["sha256"]:
                    invalid = True
                    continue
                candidate = Collection.decode(payload)
                candidate.storage_generation = sequence
                result.append((sequence, candidate))
            except (ValueError, TypeError, KeyError, UnicodeError, AttributeError, RecursionError):
                invalid = True
                continue
        if invalid or (present and not result):
            raise ValueError("No valid collection generation; originals preserved")
        return result

    def load(self):
        try:
            records = self._records()
        except RuntimeError as exc:
            raise ValueError(str(exc)) from exc
        return max(records, key=lambda row: row[0])[1] if records else None

    def commit(self, collection):
        try:
            import fcntl
        except ImportError:
            return False
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with (self.root / ".writer.lock").open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self._commit_locked(collection)
        except CollectionCommitUncertain:
            raise
        except OSError:
            return False

    def _commit_locked(self, collection):
        temporary = None
        try:
            payload = collection.encode()
            Collection.decode(payload)
            records = self._records()
            previous = max((row[0] for row in records), default=0)
            if collection.storage_generation != previous:
                return False
            generation = previous + 1
            if generation > 0xFFFFFFFF:
                return False
            body = json.dumps({"version": 1, "generation": generation, "payload": json.loads(payload),
                               "sha256": hashlib.sha256(payload.encode()).hexdigest()}, separators=(",", ":"))
            self.root.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.root / ("generation-%d.json" % (generation % 2)))
            temporary = None
            try:
                descriptor = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            except OSError as exc:
                raise CollectionCommitUncertain("Collection visibility requires reload") from exc
            collection.storage_generation = generation
            return True
        except CollectionCommitUncertain:
            raise
        except (OSError, ValueError, TypeError, RuntimeError):
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            return False
