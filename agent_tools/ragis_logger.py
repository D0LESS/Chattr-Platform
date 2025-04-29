import json
import threading
from datetime import datetime, timezone
import os

SYSTEM_VERSION = "1.0.0"
TAGGING_VERSION = "1.0.0"

class RagisLogger:
    """
    Central log/database for memory storage, retrieval, and experiment evaluation.
    For production—swap out the simple file logger for a DB/batch/remote logger as needed.
    """

    def __init__(self, log_path="ragis_events.log", pii_mask_fields=None):
        self.log_path = log_path
        self.pii_mask_fields = pii_mask_fields or []
        self._write_lock = threading.Lock()

    def utc_now_iso(self):
        """Returns current UTC timestamp."""
        return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    def log(self, event_type, data):
        """
        Main logging entrypoint.
        Scrubs/masks any configured PII fields; always adds UTC timestamp, system/tagging version.
        Thread-safe for concurrent use.
        """
        # Mask PII as configured
        masked = dict(data)
        for field in self.pii_mask_fields:
            if field in masked:
                masked[field] = self._mask_pii(masked[field])
        record = {
            "ts": self.utc_now_iso(),
            "event_type": event_type,
            "system_version": SYSTEM_VERSION,
            "tagging_version": TAGGING_VERSION,
            "data": masked
        }
        self._write(record)

    def _write(self, record):
        """Append event to log safely."""
        with self._write_lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def _mask_pii(self, value):
        """Basic PII masking—replace with XXX if a string, mask dict/lists recursively."""
        if isinstance(value, str):
            return "[MASKED]"
        elif isinstance(value, dict):
            return {k: self._mask_pii(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._mask_pii(x) for x in value]
        else:
            return None

    def log_storage_event(self, doc_id, session_id, metadata, experiment=None):
        """
        Quickly log a memory storage operation (single).
        """
        self.log("memory_store", {
            "doc_id": doc_id,
            "session_id": session_id,
            "metadata": metadata,
            "experiment": experiment,
        })

    def log_batch_storage(self, doc_ids, session_ids, metadatas, experiment=None):
        """
        Batch storage event logging.
        """
        for doc_id, session_id, meta in zip(doc_ids, session_ids, metadatas):
            self.log_storage_event(doc_id, session_id, meta, experiment)

    def log_retrieval(self, retrieval_meta):
        """
        Log memory retrieval event with all context (use for both standard and experimental queries).
        Recommended: pass full context, tags, strategies, timing, scores, etc.
        """
        self.log("memory_retrieval", retrieval_meta)

    def log_experiment(self, experiment_type, input_context, results, timing=None):
        """
        Log an explicit experiment (e.g., rarest tag vs. standard vs. pure vector).
        """
        record = {
            "experiment_type": experiment_type,
            "input_context": input_context,
            "results": results,
            "timing": timing
        }
        self.log("experiment", record)

    def rotate_log(self):
        """
        Rotates the log file (for daily or manual rotation). Closes and renames old file.
        """
        if not os.path.exists(self.log_path):
            return
        ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        new_path = f"{self.log_path}.{ts_str}"
        os.rename(self.log_path, new_path)