import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim


def _sample_negatives(pos_users, num_items, positives_by_user, neg_ratio, device):
    total = pos_users.size(0) * neg_ratio
    neg_users = pos_users.repeat_interleave(neg_ratio)
    neg_items = torch.randint(0, num_items, (total,), device=device)

    if positives_by_user:
        neg_items_cpu = neg_items.cpu().numpy()
        neg_users_cpu = neg_users.cpu().numpy()

        for i in range(total):
            u_idx = int(neg_users_cpu[i])
            pos_set = positives_by_user.get(u_idx)
            if not pos_set:
                continue
            while int(neg_items_cpu[i]) in pos_set:
                neg_items_cpu[i] = np.random.randint(0, num_items)
        neg_items = torch.tensor(neg_items_cpu, device=device)

    return neg_users, neg_items


def _bpr_loss(pos_scores, neg_scores):
    return torch.mean(F.softplus(neg_scores - pos_scores))


def train_graphsage(
    model,
    bundle,
    device,
    epochs=50,
    lr=1e-3,
    neg_sample_ratio=5,
    val_ratio=0.1,
    test_ratio=0.1,
    seed=42,
):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    model.to(device)

    data = bundle.data.to(device)
    edge_index = data["user", "interact", "item"].edge_index
    num_edges = edge_index.size(1)

    torch.manual_seed(seed)
    perm = torch.randperm(num_edges, device=device)
    test_size = int(num_edges * test_ratio)
    val_size = int(num_edges * val_ratio)
    train_size = num_edges - val_size - test_size

    train_idx = perm[:train_size]
    val_idx = perm[train_size : train_size + val_size]
    test_idx = perm[train_size + val_size :]

    num_items = data["item"].x.size(0)
    positives_by_user = bundle.interactions_by_user_idx

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        user_emb, item_emb = model(data)

        pos_edges = edge_index[:, train_idx]
        pos_users, pos_items = pos_edges[0], pos_edges[1]

        neg_users, neg_items = _sample_negatives(
            pos_users, num_items, positives_by_user, neg_sample_ratio, device
        )

        pos_scores = (user_emb[pos_users] * item_emb[pos_items]).sum(dim=1)
        neg_scores = (user_emb[neg_users] * item_emb[neg_items]).sum(dim=1)

        loss = _bpr_loss(
            pos_scores.repeat_interleave(neg_sample_ratio), neg_scores
        )

        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

    return {
        "train_idx": train_idx,
        "val_idx": val_idx,
        "test_idx": test_idx,
    }