from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import zipfile
import csv
import numpy as np
import requests
import torch
from torch_geometric.data import HeteroData


GENRES = [
    "unknown", "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery",
    "Romance", "Sci-Fi", "Thriller", "War", "Western"
]

MOVIELENS_100K_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"


@dataclass(frozen=True)
class MovieLensBundle:
    data: HeteroData
    interactions_by_user_idx: dict[int, set[int]]
    item_titles: list[str]
    item_popularity: list[float]
    movielens_item_ids: list[int]


def _download_ml100k() -> zipfile.ZipFile:
    resp = requests.get(MOVIELENS_100K_URL, timeout=60)
    resp.raise_for_status()
    return zipfile.ZipFile(BytesIO(resp.content))


def _parse_items(zf: zipfile.ZipFile):
    items = {}
    with zf.open("ml-100k/u.item") as f:
        reader = csv.reader((line.decode("latin-1") for line in f), delimiter="|")
        for row in reader:
            movie_id = int(row[0])
            title = row[1]
            genre_flags = [int(x) for x in row[5:5 + len(GENRES)]]
            items[movie_id] = {
                "title": title,
                "genre_vec": np.array(genre_flags, dtype=np.float32),
            }
    return items


def _parse_ratings(zf: zipfile.ZipFile):
    ratings = []
    with zf.open("ml-100k/u.data") as f:
        reader = csv.reader((line.decode("utf-8") for line in f), delimiter="\t")
        for row in reader:
            user_id = int(row[0])
            item_id = int(row[1])
            rating = float(row[2])
            ts = int(row[3])
            ratings.append((user_id, item_id, rating, ts))
    return ratings


def load_movielens_100k() -> MovieLensBundle:
    zf = _download_ml100k()
    items = _parse_items(zf)
    ratings = _parse_ratings(zf)

    user_ids = sorted({u for u, _, _, _ in ratings})
    item_ids = sorted(items.keys())

    user_id_to_idx = {u: i for i, u in enumerate(user_ids)}
    item_id_to_idx = {i: j for j, i in enumerate(item_ids)}

    num_users = len(user_ids)
    num_items = len(item_ids)
    num_genres = len(GENRES)

    # Aggregates
    user_counts = np.zeros(num_users, dtype=np.float32)
    user_rating_sum = np.zeros(num_users, dtype=np.float32)
    user_genre_sum = np.zeros((num_users, num_genres), dtype=np.float32)

    item_counts = np.zeros(num_items, dtype=np.float32)
    item_rating_sum = np.zeros(num_items, dtype=np.float32)

    interactions_by_user_idx = {i: set() for i in range(num_users)}

    user_edge = []
    item_edge = []

    for u_id, i_id, rating, _ in ratings:
        u_idx = user_id_to_idx[u_id]
        i_idx = item_id_to_idx[i_id]
        genre_vec = items[i_id]["genre_vec"]

        user_counts[u_idx] += 1
        user_rating_sum[u_idx] += rating
        user_genre_sum[u_idx] += genre_vec

        item_counts[i_idx] += 1
        item_rating_sum[i_idx] += rating

        interactions_by_user_idx[u_idx].add(i_idx)
        user_edge.append(u_idx)
        item_edge.append(i_idx)

    # Features
    user_avg_rating = np.divide(
        user_rating_sum, np.maximum(user_counts, 1), dtype=np.float32
    )
    user_genre_dist = np.divide(
        user_genre_sum, np.maximum(user_counts[:, None], 1), dtype=np.float32
    )
    user_features = np.concatenate(
        [user_counts[:, None], user_genre_dist, user_avg_rating[:, None]], axis=1
    ).astype(np.float32)

    item_avg_rating = np.divide(
        item_rating_sum, np.maximum(item_counts, 1), dtype=np.float32
    )
    item_popularity = np.log1p(item_counts)
    item_features = np.concatenate(
        [
            np.stack([items[i]["genre_vec"] for i in item_ids], axis=0),
            item_popularity[:, None],
            item_avg_rating[:, None],
        ],
        axis=1,
    ).astype(np.float32)

    data = HeteroData()
    data["user"].x = torch.tensor(user_features, dtype=torch.float32)
    data["item"].x = torch.tensor(item_features, dtype=torch.float32)
    edge_index = torch.tensor([user_edge, item_edge], dtype=torch.long)
    data["user", "interact", "item"].edge_index = edge_index
    data["item", "interacted_by", "user"].edge_index = edge_index.flip(0)

    item_titles = [items[i]["title"] for i in item_ids]
    item_popularity_list = item_popularity.tolist()

    return MovieLensBundle(
        data=data,
        interactions_by_user_idx=interactions_by_user_idx,
        item_titles=item_titles,
        item_popularity=item_popularity_list,
        movielens_item_ids=item_ids,
    )