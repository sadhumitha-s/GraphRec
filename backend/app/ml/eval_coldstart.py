import numpy as np
import time
from sklearn.metrics import ndcg_score


class ColdStartEvaluator:
    def __init__(self, user_emb, item_emb, interactions_by_user_idx):
        self.user_emb = user_emb
        self.item_emb = item_emb
        self.interactions_by_user_idx = interactions_by_user_idx

    def evaluate_cold_user(self, interaction_counts=(1, 3, 5), k=10):
        results = {}

        for history_size in interaction_counts:
            recalls = []
            ndcgs = []
            latencies = []

            for user_idx, items in self.interactions_by_user_idx.items():
                if len(items) < 20:
                    continue

                all_items = sorted(list(items))
                train_items = set(all_items[:history_size])
                test_items = set(all_items[history_size:])
                if not test_items:
                    continue

                start = time.time()
                scores = self.user_emb[user_idx] @ self.item_emb.T
                latencies.append(time.time() - start)

                for item_idx in train_items:
                    scores[item_idx] = -np.inf

                top_k = np.argsort(-scores)[:k]

                hits = len(set(top_k) & test_items)
                recall = hits / len(test_items)
                recalls.append(recall)

                y_true = np.isin(top_k, list(test_items)).astype(int)
                y_score = scores[top_k]
                ndcg = ndcg_score([y_true], [y_score], k=k)
                ndcgs.append(ndcg)

            results[history_size] = {
                "recall": float(np.mean(recalls)) if recalls else 0.0,
                "ndcg": float(np.mean(ndcgs)) if ndcgs else 0.0,
                "latency": float(np.mean(latencies)) if latencies else 0.0,
                "std_recall": float(np.std(recalls)) if recalls else 0.0,
            }

        return results

    def evaluate_cold_item(self, item_counts, k=10):
        cold_items = {idx for idx, cnt in item_counts.items() if cnt == 0}
        if not cold_items:
            return {"cold_item_rate": 0.0, "cold_items": 0}

        hits = []
        for user_idx in self.interactions_by_user_idx.keys():
            scores = self.user_emb[user_idx] @ self.item_emb.T
            top_k = np.argsort(-scores)[:k]
            hits.append(len(set(top_k) & cold_items) / k)

        return {
            "cold_item_rate": float(np.mean(hits)),
            "cold_items": len(cold_items),
        }