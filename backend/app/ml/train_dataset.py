import argparse
import torch

from app.db import models
from app.db import session
from app.db.session import SessionLocal
from app.ml.tmdb_dataset import load_tmdb_dataset, print_catalog_matches
from app.ml.graphsage_model import GraphSAGE
from app.ml.training import train_graphsage
from app.ml.graphsage_store import save_item_embeddings
from app.ml.graphsage_serving import normalize_title


CATALOG = [
    {"id": 101, "title": "The Matrix", "category": "Sci-Fi"},
    {"id": 102, "title": "Inception", "category": "Sci-Fi"},
    {"id": 103, "title": "The Departed", "category": "Crime"},
    {"id": 104, "title": "Toy Story", "category": "Animation"},
    {"id": 105, "title": "Gone Girl", "category": "Crime"},
    {"id": 106, "title": "Interstellar", "category": "Sci-Fi"},
    {"id": 107, "title": "Finding Nemo", "category": "Animation"},
    {"id": 108, "title": "Spirited Away", "category": "Animation"},
    {"id": 109, "title": "The Dark Knight", "category": "Action"},
    {"id": 110, "title": "Avengers: Endgame", "category": "Action"},
    {"id": 111, "title": "Mad Max: Fury Road", "category": "Action"},
    {"id": 112, "title": "John Wick", "category": "Action"},
    {"id": 113, "title": "Get Out", "category": "Horror"},
    {"id": 114, "title": "A Quiet Place", "category": "Horror"},
    {"id": 115, "title": "Superbad", "category": "Comedy"},
    {"id": 116, "title": "The Hangover", "category": "Comedy"},
    {"id": 117, "title": "The Pursuit of Happyness", "category": "Drama"},
    {"id": 118, "title": "Parasite", "category": "Drama"},
    {"id": 119, "title": "Coco", "category": "Animation"},
    {"id": 120, "title": "Dune", "category": "Sci-Fi"},
    {"id": 121, "title": "Oppenheimer", "category": "Drama"},
    {"id": 122, "title": "Barbie", "category": "Comedy"},
    {"id": 123, "title": "Killers of the Flower Moon", "category": "Crime"},
    {"id": 124, "title": "Insidious", "category": "Horror"},
]


def main():
    parser = argparse.ArgumentParser(description="Train GraphSAGE on TMDb dataset")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--neg", type=int, default=5)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--target", type=int, default=10000, help="Target movie count")
    args = parser.parse_args()

    bundle = load_tmdb_dataset(target_count=args.target)
    models.Base.metadata.create_all(bind=session.engine)
    
    print_catalog_matches(bundle, CATALOG)
    
    model = GraphSAGE(hidden_dim=64, dropout=0.2)
    device = torch.device(args.device)

    train_graphsage(
        model=model,
        bundle=bundle,
        device=device,
        epochs=args.epochs,
        lr=args.lr,
        neg_sample_ratio=args.neg,
    )

    model.eval()
    with torch.no_grad():
        user_emb, item_emb = model(bundle.data.to(device))
        item_emb = item_emb.cpu().numpy()

    title_norms = [normalize_title(t) for t in bundle.item_titles]

    db = SessionLocal()
    try:
        save_item_embeddings(
            db=db,
            tmdb_item_ids=bundle.tmdb_item_ids,
            titles=bundle.item_titles,
            title_norms=title_norms,
            embeddings=item_emb,
            popularity=bundle.item_popularity,
        )
    finally:
        db.close()

    print("Saved GraphSAGE TMDb embeddings to DB.")


if __name__ == "__main__":
    main()