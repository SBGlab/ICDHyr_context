#!/usr/bin/env python3
"""
Map genome IDs to NCBI species using taxonomy files.
"""

import sys
from pathlib import Path


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


def get_species(taxid, parent, rank, names):
    """
    Traverse up the taxonomy tree to find species.
    Returns (species_taxid, species_name).
    """
    current = taxid
    
    # First check if taxid itself is species rank
    if rank.get(current) == "species":
        return current, names.get(current, f"taxid_{current}")
    
    # Traverse up the tree
    while current in parent and current != 1:
        if rank.get(current) == "species":
            return current, names.get(current, f"taxid_{current}")
        current = parent[current]
    
    return None, None


def load_genome_taxonomy(taxonomy_file):
    """Load pg4_ncbi_taxonomy.tsv mapping genome_id -> taxid."""
    genome_taxid = {}
    
    with open(taxonomy_file) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                genome_id = parts[0].strip()
                taxid = int(parts[1].strip())
                genome_taxid[genome_id] = taxid
    
    return genome_taxid


def main():
    import os
    # Locate data files - use PROJECT_DIR env var if available (set by Nextflow)
    project_dir = os.environ.get('PROJECT_DIR')
    
    if project_dir:
        data_dir = Path(project_dir) / "data" / "metadata"
    else:
        data_dir = Path(__file__).parent.parent / "data" / "metadata"
    
    nodes_file = data_dir / "nodes.dmp"
    names_file = data_dir / "names.dmp"
    taxonomy_file = data_dir / "pg4_ncbi_taxonomy.tsv"
    
    # Load data
    print("Loading taxonomy files...", file=sys.stderr)
    parent, rank = load_nodes(nodes_file)
    names = load_names(names_file)
    genome_taxid = load_genome_taxonomy(taxonomy_file)
    
    print("Mapping genomes to species...", file=sys.stderr)
    
    # Output header
    print("genome_id\ttaxid\tspecies_taxid\tspecies_name")
    
    # Map each genome to its species
    for genome_id, taxid in sorted(genome_taxid.items()):
        species_taxid, species_name = get_species(taxid, parent, rank, names)
        
        if species_taxid is None:
            species_taxid = "NA"
            species_name = "NA"
        
        print(f"{genome_id}\t{taxid}\t{species_taxid}\t{species_name}")


if __name__ == "__main__":
    main()
