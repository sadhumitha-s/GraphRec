import argparse
import torch

from app.ml.data_loader import GraphDataLoader
from app.ml.graphsage_model import GraphSAGE
from app.ml.training import train_graphsage
from app.ml.eval_coldstart import ColdStartEvaluator


def main():
    parser = argparse.ArgumentParser(description="Train GraphSAGE from DB only")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--neg", type=int, default=5)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    loader = GraphDataLoader()
    bundle = loader.load()

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
        user_emb = user_emb.cpu().numpy()
        item_emb = item_emb.cpu().numpy()

    evaluator = ColdStartEvaluator(
        user_emb=user_emb,
        item_emb=item_emb,
        interactions_by_user_idx=bundle.interactions_by_user_idx,
    )

    cold_user_results = evaluator.evaluate_cold_user()
    print("Cold-start user results:", cold_user_results)

    item_counts = {
        idx: len(bundle.interactions_by_user_idx.get(idx, set()))
        for idx in range(item_emb.shape[0])
    }
    cold_item_results = evaluator.evaluate_cold_item(item_counts=item_counts)
    print("Cold-start item results:", cold_item_results)


if __name__ == "__main__":
    main()