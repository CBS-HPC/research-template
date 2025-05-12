import os
import re
import networkx as nx
import matplotlib.pyplot as plt

def build_script_data_graph(src_dir="src", data_dir="data"):
    """
    Scans all scripts under `src_dir` for references to files under `data_dir`,
    and builds a directed bipartite graph: script → data file.
    """
    G = nx.DiGraph()
    data_pattern = re.compile(rf"{re.escape(data_dir)}/[^\s'\";]+")  # matches e.g. data/raw/foo.csv

    for root, _, files in os.walk(src_dir):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in {".py", ".R", ".m", ".do", ".sas"}:
                continue
            script_path = os.path.join(root, fn)
            script_node = os.path.relpath(script_path)
            G.add_node(script_node, bipartite=0, type="script")

            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for match in data_pattern.findall(text):
                data_node = os.path.normpath(match)
                G.add_node(data_node, bipartite=1, type="data")
                G.add_edge(script_node, data_node)

    return G

def plot_script_data_graph(G):
    """
    Draws the bipartite graph G with scripts on the left and data on the right.
    """
    scripts = [n for n,d in G.nodes(data=True) if d["type"]=="script"]
    data    = [n for n,d in G.nodes(data=True) if d["type"]=="data"]

    pos = {}
    for i, n in enumerate(sorted(scripts)):
        pos[n] = (0, -i)
    for i, n in enumerate(sorted(data)):
        pos[n] = (1, -i)

    plt.figure(figsize=(8, max(len(scripts), len(data)) * 0.3 + 1))
    nx.draw_networkx_nodes(G, pos,
        nodelist=scripts, node_color="skyblue", node_shape="s", label="Scripts")
    nx.draw_networkx_nodes(G, pos,
        nodelist=data, node_color="lightgreen", node_shape="o", label="Data")
    nx.draw_networkx_edges(G, pos, arrowstyle="-|>", arrowsize=12)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.axis("off")
    plt.legend(scatterpoints=1)
    plt.tight_layout()
    plt.show()

def main(src_dir="src", data_dir="data"):
    """
    Build and plot the script-data dependency graph.
    """
    print(f"Scanning '{src_dir}' for scripts and '{data_dir}' for data references...")
    G = build_script_data_graph(src_dir, data_dir)
    if G.number_of_edges() == 0:
        print("No connections found between scripts and data files.")
    else:
        plot_script_data_graph(G)

if __name__ == "__main__":
    # You can override these defaults if you like:
    main(src_dir="src", data_dir="data")
