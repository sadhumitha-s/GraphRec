import matplotlib.pyplot as plt


def plot_coldstart_user(results_dict, title="Cold-Start User", output_path=None):
    history_sizes = sorted(results_dict.keys())
    recalls = [results_dict[h]["recall"] for h in history_sizes]
    ndcgs = [results_dict[h]["ndcg"] for h in history_sizes]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].plot(history_sizes, recalls, "o-", linewidth=2)
    axes[0].set_xlabel("Initial Interactions")
    axes[0].set_ylabel("Recall@10")
    axes[0].set_title(f"{title}: Recall@10")

    axes[1].plot(history_sizes, ndcgs, "s-", linewidth=2)
    axes[1].set_xlabel("Initial Interactions")
    axes[1].set_ylabel("NDCG@10")
    axes[1].set_title(f"{title}: NDCG@10")

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300)
    return fig


def plot_latency_comparison(latency_bfs, latency_pr, latency_gs, labels, output_path=None):
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    x = range(len(labels))
    ax.bar([i - 0.2 for i in x], latency_bfs, width=0.2, label="BFS")
    ax.bar(x, latency_pr, width=0.2, label="PageRank")
    ax.bar([i + 0.2 for i in x], latency_gs, width=0.2, label="GraphSAGE")

    ax.set_xlabel("Initial Interactions")
    ax.set_ylabel("Latency (s)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("Latency Comparison")
    ax.legend()

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300)
    return fig