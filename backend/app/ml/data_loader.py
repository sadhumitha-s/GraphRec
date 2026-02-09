# backend/app/ml/data_loader.py
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Tuple, Set

import numpy as np
import torch
from torch_geometric.data import HeteroData
from sqlalchemy import func

from app.db import models, crud
from app.db.session import SessionLocal


@dataclass(frozen=True)
class GraphDataBundle:
    data: HeteroData
    user_id_to_idx: Dict[int, int]
    item_id_to_idx: Dict[int, int]
    idx_to_user_id: List[int]
    idx_to_item_id: List[int]
    interactions_by_user_idx: Dict[int, Set[int]]
    interactions_by_user_id: Dict[int, Set[int]]


class GraphDataLoader:
    """
    Loads graph data and node features from the database only.
    No local files are read or written.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.genre_ids, self.genre_id_to_index = self._build_genre_index()

    def _build_genre_index(self) -> Tuple[List[int], Dict[int, int]]:
        # Build a stable genre index using GENRE_MAP values (includes Unknown=0).
        genre_ids = sorted(set(crud.GENRE_MAP.values()))
        genre_id_to_index = {gid: idx for idx, gid in enumerate(genre_ids)}
        return genre_ids, genre_id_to_index

    def load(self) -> GraphDataBundle:
        db = self.session_factory()
        try:
            # Core tables
            item_rows = db.query(models.Item.id, models.Item.category).all()
            profile_rows = db.query(models.Profile.user_id).all()
            pref_rows = db.query(models.UserPreference.user_id, models.UserPreference.genre_id).all()

            # Interactions for edges
            interaction_rows = db.query(
                models.Interaction.user_id,
                models.Interaction.item_id
            ).all()

            # Aggregates for features
            user_counts = dict(
                db.query(
                    models.Interaction.user_id,
                    func.count(models.Interaction.id)
                ).group_by(models.Interaction.user_id).all()
            )
            item_counts = dict(
                db.query(
                    models.Interaction.item_id,
                    func.count(models.Interaction.id)
                ).group_by(models.Interaction.item_id).all()
            )

        finally:
            db.close()

        # Build ID sets (include users/items even if cold-start)
        user_ids = {r[0] for r in profile_rows}
        item_ids = {r[0] for r in item_rows}

        # Include any users/items that appear only in interactions
        for u_id, i_id in interaction_rows:
            user_ids.add(u_id)
            item_ids.add(i_id)

        idx_to_user_id = sorted(user_ids)
        idx_to_item_id = sorted(item_ids)
        user_id_to_idx = {uid: idx for idx, uid in enumerate(idx_to_user_id)}
        item_id_to_idx = {iid: idx for idx, iid in enumerate(idx_to_item_id)}

        # Category map for items
        item_category = {item_id: category for item_id, category in item_rows}

        # Preferences map (user_id -> set of genre_ids)
        prefs_by_user: Dict[int, Set[int]] = defaultdict(set)
        for user_id, genre_id in pref_rows:
            if genre_id in self.genre_id_to_index:
                prefs_by_user[user_id].add(genre_id)

        # Build user feature matrix
        num_users = len(idx_to_user_id)
        num_genres = len(self.genre_ids)

        user_features = np.zeros((num_users, 1 + num_genres + 1), dtype=np.float32)

        for user_id, user_idx in user_id_to_idx.items():
            interaction_count = float(user_counts.get(user_id, 0))
            genre_vec = np.zeros(num_genres, dtype=np.float32)

            for gid in prefs_by_user.get(user_id, set()):
                genre_vec[self.genre_id_to_index[gid]] = 1.0

            # Average interaction weight: use 1.0 if any interaction exists.
            avg_weight = 1.0 if interaction_count > 0 else 0.0

            user_features[user_idx, :] = np.concatenate(
                ([interaction_count], genre_vec, [avg_weight])
            )

        # Build item feature matrix
        num_items = len(idx_to_item_id)
        item_features = np.zeros((num_items, num_genres + 2), dtype=np.float32)

        for item_id, item_idx in item_id_to_idx.items():
            category = item_category.get(item_id, "Unknown")
            genre_id = crud.get_genre_id(category)
            genre_idx = self.genre_id_to_index.get(genre_id, self.genre_id_to_index[0])
            genre_vec = np.zeros(num_genres, dtype=np.float32)
            genre_vec[genre_idx] = 1.0

            interaction_count = float(item_counts.get(item_id, 0))
            popularity = np.log1p(interaction_count)
            avg_rating = 0.0  # Placeholder: no explicit ratings in schema

            item_features[item_idx, :] = np.concatenate(
                (genre_vec, [popularity, avg_rating])
            )

        # Edge index
        user_edge_idx = []
        item_edge_idx = []
        interactions_by_user_idx: Dict[int, Set[int]] = defaultdict(set)
        interactions_by_user_id: Dict[int, Set[int]] = defaultdict(set)

        for user_id, item_id in interaction_rows:
            if user_id not in user_id_to_idx or item_id not in item_id_to_idx:
                continue
            u_idx = user_id_to_idx[user_id]
            i_idx = item_id_to_idx[item_id]
            user_edge_idx.append(u_idx)
            item_edge_idx.append(i_idx)

            interactions_by_user_idx[u_idx].add(i_idx)
            interactions_by_user_id[user_id].add(item_id)

        edge_index = torch.tensor([user_edge_idx, item_edge_idx], dtype=torch.long)

        # Build HeteroData
        data = HeteroData()
        data["user"].x = torch.tensor(user_features, dtype=torch.float32)
        data["item"].x = torch.tensor(item_features, dtype=torch.float32)

        data["user", "interact", "item"].edge_index = edge_index
        data["item", "interacted_by", "user"].edge_index = edge_index.flip(0)

        return GraphDataBundle(
            data=data,
            user_id_to_idx=user_id_to_idx,
            item_id_to_idx=item_id_to_idx,
            idx_to_user_id=idx_to_user_id,
            idx_to_item_id=idx_to_item_id,
            interactions_by_user_idx=interactions_by_user_idx,
            interactions_by_user_id=interactions_by_user_id,
        )