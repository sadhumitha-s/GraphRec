import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv


class GraphSAGE(nn.Module):
    def __init__(self, hidden_dim: int = 64, dropout: float = 0.2):
        super().__init__()

        self.conv1 = HeteroConv(
            {
                ("user", "interact", "item"): SAGEConv((-1, -1), hidden_dim),
                ("item", "interacted_by", "user"): SAGEConv((-1, -1), hidden_dim),
            },
            aggr="mean",
        )
        self.conv2 = HeteroConv(
            {
                ("user", "interact", "item"): SAGEConv((-1, -1), hidden_dim),
                ("item", "interacted_by", "user"): SAGEConv((-1, -1), hidden_dim),
            },
            aggr="mean",
        )
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, data):
        x_dict = self.conv1(data.x_dict, data.edge_index_dict)
        x_dict = {k: F.relu(v) for k, v in x_dict.items()}
        x_dict = {k: self.dropout(v) for k, v in x_dict.items()}

        x_dict = self.conv2(x_dict, data.edge_index_dict)
        x_dict = {k: F.relu(v) for k, v in x_dict.items()}

        return x_dict["user"], x_dict["item"]