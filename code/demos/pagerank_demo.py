#!/usr/bin/env python3
"""
PageRank link analysis — working demonstration.
Related patent: US 6,285,999 "Method for node ranking in a linked
database" (Page / Stanford, assignee Google). Pure Python, no
dependencies. Power-iteration on a small 5-node graph.
"""


def pagerank(graph, damping=0.85, iterations=50):
    nodes = list(graph)
    n = len(nodes)
    rank = {node: 1.0 / n for node in nodes}
    for _ in range(iterations):
        # Rank held by dead-end nodes (no outlinks) is redistributed
        # evenly — this keeps total rank mass conserved at 1.0.
        dangling = sum(rank[src] for src in nodes if not graph[src])
        new_rank = {}
        for node in nodes:
            inbound = sum(
                rank[src] / len(graph[src])
                for src in nodes
                if node in graph[src] and graph[src]
            )
            new_rank[node] = (1 - damping) / n + damping * (inbound + dangling / n)
        rank = new_rank
    return rank


def pagerank_demo():
    # A tiny web: A links to B and C; B links to C; C links to A;
    # D links to C; E is a dead end nobody links to.
    graph = {
        "A": ["B", "C"],
        "B": ["C"],
        "C": ["A"],
        "D": ["C"],
        "E": [],
    }
    ranks = pagerank(graph)
    print("PageRank scores (patent US 6,285,999 method):")
    for node, score in sorted(ranks.items(), key=lambda kv: -kv[1]):
        print(f"  {node}: {score:.4f}")
    total = sum(ranks.values())
    assert abs(total - 1.0) < 1e-6, "ranks must sum to 1"
    assert ranks["C"] > ranks["E"], "well-linked node must outrank dead end"
    print("Self-checks OK: ranks sum to 1, C outranks isolated E.")


if __name__ == "__main__":
    pagerank_demo()
    print("Self-test: PASS")
