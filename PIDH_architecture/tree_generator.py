import pandas as pd
from ete3 import NCBITaxa, Tree, TreeStyle, NodeStyle

# Load your file
df = pd.read_csv("results/final_architecture_summary_with_habitat.csv")  # adjust separator if needed

# Ensure taxid is int
df["taxid"] = df["taxid"].astype(int)

# Initialize taxonomy
ncbi = NCBITaxa()

# Get topology (this builds the phylogenetic tree)
taxids = df["taxid"].unique().tolist()
tree = ncbi.get_topology(taxids)

# Map architecture_type to taxid
arch_map = dict(zip(df["taxid"], df["genome_predominant_architecture_type"]))

# Define colors for each architecture_type
unique_types = df["genome_predominant_architecture_type"].unique()
color_palette = ["red", "blue", "green", "orange", "purple", "cyan"]

color_map = {t: color_palette[i % len(color_palette)] 
             for i, t in enumerate(unique_types)}

# Traverse tree and color branches
for node in tree.traverse():
    if node.is_leaf():
        taxid = int(node.name)
        arch = arch_map.get(taxid, "unknown")
        color = color_map.get(arch, "black")

        nstyle = NodeStyle()
        nstyle["fgcolor"] = color
        nstyle["size"] = 10
        node.set_style(nstyle)

        # Optional: rename leaf with architecture info
        node.name = f"{taxid} | {arch}"
    else:
        # internal nodes (optional styling)
        nstyle = NodeStyle()
        nstyle["fgcolor"] = "black"
        node.set_style(nstyle)

# Tree visualization
ts = TreeStyle()
ts.show_leaf_name = True
ts.title.add_face("IDH Architecture Phylogeny", column=0)

tree.show(tree_style=ts)

# Save outputs
tree.write(outfile="idh_tree.nw")
tree.render("idh_tree.png", tree_style=ts, w=1200)
