import chromadb

from datetime import datetime, timedelta, timezone
import uuid
import json
import os
from agent_tools.ragis_logger import RagisLogger  # <-- Import here

SYSTEM_VERSION = "1.0.0"
TAGGING_VERSION = "1.0.0"

class MemoryStore:
    def __init__(self, db_path='datastore', collection_name='memory', synonyms_path="synonyms.json", log_path="ragis_events.log"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name

        self.synonym_map = self._load_synonym_map(synonyms_path)
        self.synonyms_path = synonyms_path

        # Central logger (PII: redact raw_text if needed)
        self.logger = RagisLogger(log_path=log_path, pii_mask_fields=['raw_text'])

    def _load_synonym_map(self, path):
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def reload_synonym_map(self):
        self.synonym_map = self._load_synonym_map(self.synonyms_path)

    def normalize_metatags(self, raw_tags):
        return [self.synonym_map.get(tag, tag).lower() for tag in raw_tags]

    def utc_now_iso(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    def add_memory(self, raw_text, embedding, major_category, metatags,
                   session_id, timestamp=None, tag_freq_window=None):
        norm_metatags = self.normalize_metatags(metatags)
        datestamp = timestamp or self.utc_now_iso()
        freq_90d = tag_freq_window or {}

        metadata = {
            "major_category": major_category.lower(),
            "metatags": norm_metatags,
            "session_id": session_id,
            "timestamp": datestamp,
            "system_version": SYSTEM_VERSION,
            "tagging_version": TAGGING_VERSION,
            "tag_freq_90d": freq_90d,
        }

        doc_id = str(uuid.uuid4())

        # Strict check for correct embeddings
        if embedding is None:
            raise ValueError("Embedding cannot be None. Provide a real embedding vector for the memory.")
        if isinstance(embedding, str) or not isinstance(embedding, (list, tuple)):
            raise ValueError(f"Embedding must be a list of numbers (floats or ints), not {type(embedding)}.")
        if not all(isinstance(x, (float, int)) for x in embedding):
            raise ValueError("All elements in embedding must be float or int.")

        self.collection.add([embedding], [doc_id], metadatas=[metadata], documents=[raw_text])
        # Centralized logging
        self.logger.log_storage_event(doc_id, session_id, metadata)

    def add_memories_batch(self, memory_entries):
        embeddings, ids, metadatas, documents = [], [], [], []
        doc_ids, session_ids, metas = [], [], []
        for entry in memory_entries:
            norm_metatags = self.normalize_metatags(entry["metatags"])
            datestamp = entry.get("timestamp") or self.utc_now_iso()
            freq_90d = entry.get("tag_freq_window", {})

            metadata = {
                "major_category": entry["major_category"].lower(),
                "metatags": norm_metatags,
                "session_id": entry["session_id"],
                "timestamp": datestamp,
                "system_version": SYSTEM_VERSION,
                "tagging_version": TAGGING_VERSION,
                "tag_freq_90d": freq_90d,
            }
            doc_id = str(uuid.uuid4())
            embeddings.append(entry["embedding"])
            ids.append(doc_id)
            metadatas.append(metadata)
            documents.append(entry["raw_text"])
            doc_ids.append(doc_id)
            session_ids.append(entry["session_id"])
            metas.append(metadata)
        self.collection.add(embeddings, ids, metadatas, documents)
        self.logger.log_batch_storage(doc_ids, session_ids, metas)

    def retro_tag_memory(self, session_id, tag_extractor_fn):
        results = self.collection.get(where={"session_id": session_id})
        updated_docs = []
        error_docs = []
        for doc, meta, emb, doc_id in zip(
                results['documents'],
                results['metadatas'],
                results['embeddings'],
                results['ids']):
            try:
                major_category, metatags = tag_extractor_fn(doc)
                norm_metatags = self.normalize_metatags(metatags)
                meta['major_category'] = major_category.lower()
                meta['metatags'] = norm_metatags
                meta['tagging_version'] = TAGGING_VERSION
                self.collection.update(ids=[doc_id],
                                      metadatas=[meta],
                                      embeddings=[emb],
                                      documents=[doc])
                updated_docs.append(doc_id)
            except Exception as e:
                error_docs.append({"doc_id": doc_id, "error": str(e)})
        # Log retro-tag results
        self.logger.log("retro_tag_complete", {
            "session_id": session_id,
            "updated_doc_ids": updated_docs,
            "errors": error_docs,
            "tagging_version": TAGGING_VERSION,
        })

    def verify_metatag_completeness(self, session_id: str) -> bool:
        """
        Check if all memories for a session have complete metatag info and correct tagging version.
        """
        results = self.collection.get(where={'session_id': session_id})
        for meta in results["metadatas"]:
            if ('major_category' not in meta or not meta['major_category']
                or 'metatags' not in meta or not meta['metatags']
                or meta.get('tagging_version', '') != TAGGING_VERSION):
                return False
        return True

    def get_tag_freqs(self, metatag: str, days: int = 90) -> int:
        """
        Return the count of memories with this metatag in the last N days.
        Uses $contains for partial match in ChromaDB (metatags is a list).
        """
        results = self.collection.get(where={"metatags": {"$contains": metatag}})
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        count = 0
        for meta in results["metadatas"]:
            try:
                t = datetime.fromisoformat(meta["timestamp"])
                if (now - t).days <= days:
                    count += 1
            except Exception as e:
                self.logger.log("tag_freqs_parse_error", {"meta": meta, "error": str(e)})
                continue
        return count