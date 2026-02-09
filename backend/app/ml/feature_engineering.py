import numpy as np
from app.ml.data_loader import GraphDataLoader


class FeatureEngineer:
    """
    Thin wrapper around GraphDataLoader to avoid duplicate feature logic.
    """

    def __init__(self, session_factory=None):
        self.loader = GraphDataLoader(session_factory=session_factory)

    def build_all_features(self):
        bundle = self.loader.load()
        user_features = bundle.data["user"].x.cpu().numpy()
        item_features = bundle.data["item"].x.cpu().numpy()
        return user_features, item_features, bundle.user_id_to_idx, bundle.item_id_to_idx

    def get_user_features(self, user_id: int) -> np.ndarray:
        bundle = self.loader.load()
        idx = bundle.user_id_to_idx.get(user_id)
        if idx is None:
            return np.array([], dtype=np.float32)
        return bundle.data["user"].x[idx].cpu().numpy()

    def get_item_features(self, item_id: int) -> np.ndarray:
        bundle = self.loader.load()
        idx = bundle.item_id_to_idx.get(item_id)
        if idx is None:
            return np.array([], dtype=np.float32)
        return bundle.data["item"].x[idx].cpu().numpy()