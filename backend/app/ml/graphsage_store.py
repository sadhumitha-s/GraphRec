import numpy as np
from sqlalchemy.orm import Session
from app.db import models


def save_item_embeddings(
    db: Session,
    tmdb_item_ids,
    titles,
    title_norms,
    embeddings,
    popularity,
):
    db.query(models.GraphSageItem).delete()
    for idx, movie_id in enumerate(tmdb_item_ids):
        emb_bytes = embeddings[idx].astype(np.float32).tobytes()
        row = models.GraphSageItem(
            tmdb_id=movie_id,
            title=titles[idx],
            title_norm=title_norms[idx],
            embedding=emb_bytes,
            popularity=float(popularity[idx]),
        )
        db.add(row)
    db.merge(models.GraphSageMeta(key="embedding_dim", value=str(embeddings.shape[1])))
    db.commit()