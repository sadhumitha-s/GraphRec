import argparse
import torch

from app.db import models
from app.db import session
from app.db.session import SessionLocal
from app.ml.movielens_dataset import load_movielens_100k
from app.ml.graphsage_model import GraphSAGE
from app.ml.training import train_graphsage
from app.ml.graphsage_store import save_item_embeddings
from app.ml.graphsage_serving import normalize_title


def main():
    parser = argparse.ArgumentParser(description="Train GraphSAGE on MovieLens and store embeddings in DB")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--neg", type=int, default=5)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    bundle = load_movielens_100k()
    models.Base.metadata.create_all(bind=session.engine)
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
            movielens_item_ids=bundle.movielens_item_ids,
            titles=bundle.item_titles,
            title_norms=title_norms,
            embeddings=item_emb,
            popularity=bundle.item_popularity,
        )
    finally:
        db.close()

    print("Saved GraphSAGE MovieLens embeddings to DB.")


if __name__ == "__main__":
    main()