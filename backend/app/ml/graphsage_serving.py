from __future__ import annotations

import re
import threading
import numpy as np
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import models, crud


@dataclass(frozen=True)
class GraphSageIndex:
    embeddings: np.ndarray
    title_to_idx: dict[str, int]
    popularity: np.ndarray


_LOCK = threading.Lock()
_CACHE: GraphSageIndex | None = None


def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"\(\d{4}\)", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _load_index(db: Session) -> GraphSageIndex | None:
    rows = db.query(models.GraphSageItem).all()
    if not rows:
        return None

    meta = db.query(models.GraphSageMeta).filter(models.GraphSageMeta.key == "embedding_dim").first()
    emb_dim = int(meta.value) if meta else None

    embeddings = []
    title_to_idx = {}
    popularity = []

    for idx, row in enumerate(rows):
        if emb_dim is None:
            emb_dim = int(len(row.embedding) / 4)
        emb = np.frombuffer(row.embedding, dtype=np.float32, count=emb_dim)
        embeddings.append(emb)
        title_to_idx[row.title_norm] = idx
        popularity.append(float(row.popularity))

    return GraphSageIndex(
        embeddings=np.vstack(embeddings),
        title_to_idx=title_to_idx,
        popularity=np.array(popularity, dtype=np.float32),
    )


def get_graphsage_index() -> GraphSageIndex | None:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    with _LOCK:
        if _CACHE is not None:
            return _CACHE
        db = SessionLocal()
        try:
            _CACHE = _load_index(db)
        finally:
            db.close()
    return _CACHE


def recommend_graphsage_for_user(db: Session, user_id: int, k: int):
    index = get_graphsage_index()
    if index is None:
        return []

    item_map = crud.get_item_map(db)
    candidates = []
    for db_item_id, details in item_map.items():
        norm = normalize_title(details["title"])
        idx = index.title_to_idx.get(norm)
        if idx is not None:
            candidates.append((db_item_id, idx))

    if not candidates:
        return []

    seen_ids = crud.get_user_interacted_ids(db, user_id)
    user_item_idxs = [idx for db_id, idx in candidates if db_id in seen_ids]

    if user_item_idxs:
        user_emb = index.embeddings[user_item_idxs].mean(axis=0)
        candidate_idxs = [idx for _, idx in candidates]
        scores = index.embeddings[candidate_idxs] @ user_emb
        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for (db_item_id, _), _score in scored:
            if db_item_id not in seen_ids:
                results.append(db_item_id)
            if len(results) >= k:
                break
        return results

    # Cold-start: rank by MovieLens popularity
    scored = list(zip(candidates, index.popularity[[idx for _, idx in candidates]]))
    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for (db_item_id, _), _score in scored:
        if db_item_id not in seen_ids:
            results.append(db_item_id)
        if len(results) >= k:
            break
    return results