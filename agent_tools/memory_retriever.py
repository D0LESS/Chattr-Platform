import chromadb
from datetime import datetime, timedelta, timezone
import numpy as np
import json
import os
from agent_tools.ragis_logger import RagisLogger  # <--- central logger

SYSTEM_VERSION = "1.0.0"
TAGGING_VERSION = "1.0.0"

class MemoryRetriever:
    def __init__(
        self, 
        db_path='datastore', 
        collection_name='memory', 
        synonyms_path="synonyms.json", 
        log_path="ragis_events.log"
    ):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)

        self.log_path = log_path
        self.logger = RagisLogger(log_path=log_path, pii_mask_fields=['query_text'])

        # Load synonym map just as in MemoryStore
        self.synonym_map = self._load_synonym_map(synonyms_path)
        self.synonyms_path = synonyms_path

    def _load_synonym_map(self, path):
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def reload_synonym_map(self):
        self.synonym_map = self._load_synonym_map(self.synonyms_path)

    def normalize_metatags(self, raw_tags):
        return [self.synonym_map.get(tag, tag).lower() for tag in raw_tags]

    def utc_now(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc)

    def retrieve_memories(
        self, 
        query_embedding, 
        context_window_metatags: list, 
        query_text: str, 
        use_recent_days=90, 
        min_tag_freq=10, 
        experiment_mode=None,  # None/'pure'/'rarest'
        log_context=None
    ):
        """
        Retrieve matching memories using:
        -  major category/tag narrowing,
        -  tag overlap within the context window + recency subfilter,
        -  optional experiment (pure vector, rarest tag)
        """
        now = self.utc_now()
        # Normalize context tags
        all_context_tags = self.normalize_metatags(context_window_metatags)

        # Get frequency counts for all context tags
        tag_counts_90d = {}
        for tag in set(all_context_tags):
            tag_counts_90d[tag] = self.get_tag_freqs(tag, days=use_recent_days)

        # Only keep tags that meet the minimum freq
        qualifying_tags = [tag for tag in all_context_tags if tag_counts_90d.get(tag, 0) >= min_tag_freq]

        # Choose filtering strategy
        major_cats = self._get_major_categories(qualifying_tags)
        filter_query = None

        # Branch by experiment mode
        if experiment_mode == "pure":
            # No metatag narrowing, just vector similarity
            filter_query = {}
            tag_strategy = "pure"
        elif experiment_mode == "rarest":
            tag, c = self._get_rarest_qualifying_tag(tag_counts_90d, min_tag_freq)
            filter_query = {"metatags": tag} if tag else {}
            tag_strategy = f"rarest:{tag}" if tag else "none"
        else:
            # Default: restrict by major_category and metatags
            if major_cats:
                filter_query = {"major_category": {"$in": major_cats}}
                if qualifying_tags:
                    filter_query["metatags"] = {"$in": qualifying_tags}
            else:
                filter_query = {}

            tag_strategy = "standard"

        # Always add time preference: only within recent N days if possible
        ids, metadatas, scores, docs = [], [], [], []

        # ChromaDB doesn't (yet) do direct timestamp filtering server-side, so fetch and filter here
        candidate_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=30,  # tune as needed
            where=filter_query,
            include=['documents', 'metadatas', 'distances']
        )

        # Manual post-filter by recency
        for idx, meta in enumerate(candidate_results.get('metadatas', [])):
            ts = meta.get("timestamp")
            if not ts: continue
            t = datetime.fromisoformat(ts)
            if (now - t).days <= use_recent_days:
                ids.append(candidate_results['ids'][idx])
                metadatas.append(meta)
                docs.append(candidate_results["documents"][idx])
                scores.append(candidate_results['distances'][idx])

        # Prepare for backward analysis/logging
        out_record = {
            "timestamp": now.isoformat(),
            "context_tags": all_context_tags,
            "context_tag_counts_90d": tag_counts_90d,
            "qualifying_tags": qualifying_tags,
            "major_cats": major_cats,
            "filter_query": filter_query,
            "strategy": tag_strategy,
            "experiment_mode": experiment_mode or "standard",
            "retrieved_ids": ids,
            "retrieved_scores": scores,
            "retrieved_metadatas": metadatas,
            "retrieved_docs": docs,
            "query_text": query_text,
            "system_version": SYSTEM_VERSION,
            "tagging_version": TAGGING_VERSION,
            "log_context": log_context,
            "result_count": len(ids)
        }
        # Centralized RagisLogger
        self.logger.log_retrieval(out_record)

        return docs, metadatas, scores

    def get_tag_freqs(self, metatag, days=90):
        """
        Return the count of memories with this metatag in the last N days.
        """
        results = self.collection.get(where={"metatags": {"$contains": metatag}})
        now = self.utc_now()
        count = 0
        for meta in results.get("metadatas", []):
            ts = meta.get("timestamp")
            if not ts:
                continue
            t = datetime.fromisoformat(ts)
            if (now - t).days <= days:
                count += 1
        return count

    def _get_major_categories(self, tags):
        """
        Collect all unique major_categories present for the set of tags.
        """
        cats = set()
        for tag in set(tags):
            results = self.collection.get(where={"metatags": {"$contains": tag}})
            for meta in results.get("metadatas", []):
                cat = meta.get("major_category")
                if cat:
                    cats.add(cat)
        return list(cats)

    def _get_rarest_qualifying_tag(self, tag_counts: dict, min_tag_freq: int):
        """
        Given tag:count pairs, return rarest tag meeting threshold.
        """
        qualifying = [(tag, c) for tag, c in tag_counts.items() if c >= min_tag_freq]
        if not qualifying: return None, None
        return sorted(qualifying, key=lambda x: x[1])[0]