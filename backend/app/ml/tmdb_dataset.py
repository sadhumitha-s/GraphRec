from __future__ import annotations

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Set
import time

import numpy as np
import requests
import torch
from torch_geometric.data import HeteroData


TMDB_GENRE_MAP = {
    "Action": 28,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Drama": 18,
    "Horror": 27,
    "Sci-Fi": 878,
}

GENRE_ID_TO_NAME = {v: k for k, v in TMDB_GENRE_MAP.items()}

CACHE_DIR = Path(__file__).parent / "data"
CACHE_FILE = CACHE_DIR / "tmdb_cache.jsonl"


@dataclass(frozen=True)
class TMDbBundle:
    data: HeteroData
    interactions_by_user_idx: Dict[int, Set[int]]
    item_titles: List[str]
    item_popularity: List[float]
    tmdb_item_ids: List[int]
    genre_names: List[str]


def _fetch_movies_from_tmdb(api_key: str, target_count: int = 10000) -> List[dict]:
    CACHE_DIR.mkdir(exist_ok=True)
    
    if CACHE_FILE.exists():
        print(f"Loading cached TMDb data from {CACHE_FILE}")
        movies = []
        with open(CACHE_FILE, "r") as f:
            for line in f:
                movies.append(json.loads(line))
        return movies
    
    print(f"Fetching ~{target_count} movies from TMDb API (slow, rate-limit safe)...")
    movies = []
    seen_ids = set()
    
    per_genre_target = target_count // len(TMDB_GENRE_MAP)
    
    for genre_name, genre_id in TMDB_GENRE_MAP.items():
        print(f"  Fetching {genre_name} (target: {per_genre_target}, ~10s per page)...")
        page = 1
        genre_count = 0
        empty_pages = 0
        
        while genre_count < per_genre_target and page <= 50 and empty_pages < 2:
            url = "https://api.themoviedb.org/3/discover/movie"
            params = {
                "api_key": api_key,
                "with_genres": genre_id,
                "primary_release_date.gte": "1995-01-01",
                "primary_release_date.lte": "2023-12-31",
                "sort_by": "popularity.desc",
                "page": page,
                "vote_count.gte": 50,
            }
            
            try:
                print(f"    Page {page}...", end="", flush=True)
                resp = requests.get(url, params=params, timeout=30)
                
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 60))
                    print(f" rate limited, waiting {wait}s")
                    time.sleep(wait + 5)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                
                results = data.get("results", [])
                if not results:
                    empty_pages += 1
                    print(" empty")
                    page += 1
                    time.sleep(2)
                    continue
                
                empty_pages = 0
                page_count = 0
                
                for movie in results:
                    if movie["id"] in seen_ids:
                        continue
                    seen_ids.add(movie["id"])
                    
                    movies.append({
                        "tmdb_id": movie["id"],
                        "title": movie["title"],
                        "genre_ids": movie["genre_ids"],
                        "popularity": movie["popularity"],
                        "page_genre": genre_name,
                        "page_num": page,
                    })
                    genre_count += 1
                    page_count += 1
                    
                    if genre_count >= per_genre_target:
                        break
                
                print(f" ok ({page_count} new)")
                page += 1
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                print(f" error: {e}")
                time.sleep(30)
        
        print(f"    Total {genre_name}: {genre_count} movies\n")
    
    if not movies:
        raise RuntimeError("Failed to fetch any movies from TMDb API")
    
    with open(CACHE_FILE, "w") as f:
        for movie in movies:
            f.write(json.dumps(movie) + "\n")
    
    print(f"Cached {len(movies)} movies to {CACHE_FILE}")
    return movies


def load_tmdb_dataset(api_key: str = None, target_count: int = 10000) -> TMDbBundle:
    if api_key is None:
        api_key = os.getenv("TMDB_API_KEY")
        if not api_key:
            raise ValueError("TMDB_API_KEY not set in environment")
    
    movies = _fetch_movies_from_tmdb(api_key, target_count)
    
    tmdb_ids = sorted({m["tmdb_id"] for m in movies})
    item_id_to_idx = {tid: i for i, tid in enumerate(tmdb_ids)}
    
    pseudo_users = {}
    user_idx = 0
    for movie in movies:
        key = (movie["page_genre"], movie["page_num"])
        if key not in pseudo_users:
            pseudo_users[key] = user_idx
            user_idx += 1
    
    num_users = len(pseudo_users)
    num_items = len(tmdb_ids)
    num_genres = len(TMDB_GENRE_MAP)
    
    user_counts = np.zeros(num_users, dtype=np.float32)
    user_genre_sum = np.zeros((num_users, num_genres), dtype=np.float32)
    
    item_counts = np.zeros(num_items, dtype=np.float32)
    item_genre_vecs = np.zeros((num_items, num_genres), dtype=np.float32)
    item_popularity = np.zeros(num_items, dtype=np.float32)
    
    interactions_by_user_idx = {i: set() for i in range(num_users)}
    
    user_edge = []
    item_edge = []
    
    for movie in movies:
        tmdb_id = movie["tmdb_id"]
        item_idx = item_id_to_idx[tmdb_id]
        user_id = pseudo_users[(movie["page_genre"], movie["page_num"])]
        
        genre_vec = np.zeros(num_genres, dtype=np.float32)
        for gid in movie["genre_ids"]:
            if gid in GENRE_ID_TO_NAME:
                genre_idx = list(TMDB_GENRE_MAP.values()).index(gid)
                genre_vec[genre_idx] = 1.0
        
        item_genre_vecs[item_idx] = genre_vec
        item_popularity[item_idx] = movie["popularity"]
        
        user_counts[user_id] += 1
        user_genre_sum[user_id] += genre_vec
        item_counts[item_idx] += 1
        
        interactions_by_user_idx[user_id].add(item_idx)
        user_edge.append(user_id)
        item_edge.append(item_idx)
    
    user_genre_dist = np.divide(
        user_genre_sum, np.maximum(user_counts[:, None], 1), dtype=np.float32
    )
    user_features = np.concatenate(
        [user_counts[:, None], user_genre_dist], axis=1
    ).astype(np.float32)
    
    item_popularity_norm = np.log1p(item_popularity)
    item_features = np.concatenate(
        [item_genre_vecs, item_popularity_norm[:, None]], axis=1
    ).astype(np.float32)
    
    data = HeteroData()
    data["user"].x = torch.tensor(user_features, dtype=torch.float32)
    data["item"].x = torch.tensor(item_features, dtype=torch.float32)
    edge_index = torch.tensor([user_edge, item_edge], dtype=torch.long)
    data["user", "interact", "item"].edge_index = edge_index
    data["item", "interacted_by", "user"].edge_index = edge_index.flip(0)
    
    movie_dict = {m["tmdb_id"]: m for m in movies}
    item_titles = [movie_dict[tid]["title"] for tid in tmdb_ids]
    item_popularity_list = item_popularity.tolist()
    
    genre_names = []
    for tid in tmdb_ids:
        gids = movie_dict[tid]["genre_ids"]
        names = [GENRE_ID_TO_NAME.get(g, "Unknown") for g in gids if g in GENRE_ID_TO_NAME]
        genre_names.append(names[0] if names else "Unknown")
    
    return TMDbBundle(
        data=data,
        interactions_by_user_idx=interactions_by_user_idx,
        item_titles=item_titles,
        item_popularity=item_popularity_list,
        tmdb_item_ids=tmdb_ids,
        genre_names=genre_names,
    )


def print_catalog_matches(bundle: TMDbBundle, catalog: List[dict]):
    print("\nExact TMDb Titles for Your Catalog:\n" + "="*80)
    
    title_map = {t.lower(): (t, g, tid) for t, g, tid in zip(
        bundle.item_titles, bundle.genre_names, bundle.tmdb_item_ids
    )}
    
    for item in catalog:
        search_title = item["title"].lower()
        if search_title in title_map:
            exact_title, genre, tmdb_id = title_map[search_title]
            print(f'{item["id"]:3d} | {exact_title:40s} | {genre:10s} | TMDb:{tmdb_id}')
        else:
            matches = [t for t in title_map.keys() if search_title in t or t in search_title]
            if matches:
                best = matches[0]
                exact_title, genre, tmdb_id = title_map[best]
                print(f'{item["id"]:3d} | {exact_title:40s} | {genre:10s} | TMDb:{tmdb_id} (fuzzy)')
            else:
                print(f'{item["id"]:3d} | {item["title"]:40s} | NOT FOUND')
    
    print("="*80)