#!/usr/bin/env python3
"""
Map genome IDs to NCBI kingdoms using taxonomy files.
"""

import sys
from pathlib import Path
from collections import defaultdict


def load_nodes(nodes_file):
    """Load nodes.dmp and create parent lookup + rank lookup."""
    parent = {}
    rank = {}
    
    with open(nodes_file) as f:
        for line in f:
            parts = [x.strip() for x in line.split('|')]
            taxid = int(parts[0])
            parent_taxid = int(parts[1])
            node_rank = parts[2]
            
            parent[taxid] = parent_taxid
            rank[taxid] = node_rank
    
    return parent, rank


def load_names(names_file):
    """Load names.dmp and extract scientific names."""
    names = {}
    
    with open(names_file) as f:
        for line in f:
            parts = [x.strip() for x in line.split('|')]
            taxid = int(parts[0])
            name = parts[1]
            name_class = parts[3]
            
            # Store scientific names
            if name_class == "scientific name":
                names[taxid] = name
    
    return names


def get_kingdom(taxid, parent, rank, names):
    """
    Traverse up the taxonomy tree to find kingdom.
    Returns (kingdom_taxid, kingdom_name).
    """
    current = taxid
    
    # Traverse up until we find kingdom rank or reach root
    while current in parent and current != 1:
        current_rank = rank.get(current, "")
        
        if current_rank == "kingdom":
            kingdom_name = names.get(current, f"taxid_{current}")
            return current, kingdom_name
        
        # Move to parent
        current = parent[current]
    
    # If we didn't find kingdom, return None
    return None, None


def load_genome_taxonomy(taxonomy_file):
    """Load genome -> taxid mapping from pg4_ncbi_taxonomy.tsv."""
    genome_taxid = {}
    
    with open(taxonomy_file) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                genome_id = parts[0]
                taxid = int(parts[1])
                genome_taxid[genome_id] = taxid
    
    return genome_taxid


def main():
    import os
    # Locate data files - use PROJECT_DIR env var if available (set by Nextflow)
    project_dir = os.environ.get('PROJECT_DIR')
    
    if project_dir:
        nodes_file = Path(project_dir) / "data" / "metadata" / "nodes.dmp"
        names_file = Path(project_dir) / "data" / "metadata" / "names.dmp"
        taxonomy_file = Path(project_dir) / "data" / "metadata" / "pg4_ncbi_taxonomy.tsv"
    else:
        nodes_file = Path("data/metadata/nodes.dmp")
        names_file = Path("data/metadata/names.dmp")
        taxonomy_file = Path("data/metadata/pg4_ncbi_taxonomy.tsv")
    
    if not all([nodes_file.exists(), names_file.exists(), taxonomy_file.exists()]):
        print("ERROR: Missing required files:", file=sys.stderr)
        print(f"  {nodes_file}: {nodes_file.exists()}", file=sys.stderr)
        print(f"  {names_file}: {names_file.exists()}", file=sys.stderr)
        print(f"  {taxonomy_file}: {taxonomy_file.exists()}", file=sys.stderr)
        sys.exit(1)
    
    print("Loading taxonomy files...", file=sys.stderr)
    parent, rank = load_nodes(nodes_file)
    names = load_names(names_file)
    genome_taxid = load_genome_taxonomy(taxonomy_file)
    
    print("Mapping genomes to kingdoms...", file=sys.stderr)
    
    # Create output with headers
    print("genome_id\ttaxid\tkingdom_taxid\tkingdom_name")
    
    for genome_id, taxid in sorted(genome_taxid.items()):
        kingdom_taxid, kingdom_name = get_kingdom(taxid, parent, rank, names)
        
        if kingdom_taxid is None:
            kingdom_taxid = "NA"
            kingdom_name = "NA"
        
        print(f"{genome_id}\t{taxid}\t{kingdom_taxid}\t{kingdom_name}")


if __name__ == "__main__":
    main()
