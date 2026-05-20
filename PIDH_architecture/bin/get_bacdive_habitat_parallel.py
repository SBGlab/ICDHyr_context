import argparse
import pandas as pd
import numpy as np
import collections
import functools
import operator
import time
import os
import bacdive
from ete3 import NCBITaxa
from Bio import Entrez

# Configuration
Entrez.email = "agargantilla@cnb.csic.es"
ncbi = NCBITaxa()

def get_habitats(client, taxid):
    sources_none = {'soil counts': None, 'aquatic counts': None, 'animal counts': None, 'plant counts': None}
    if not taxid or str(taxid) == "None" or str(taxid) == "nan":
        return sources_none
    try:
        count = client.search(taxonomy=str(taxid))
        if count == 0:
            lineage = ncbi.get_lineage(taxid)
            ranks = ncbi.get_rank(lineage)
            species_taxid = [tid for tid, rank in ranks.items() if rank == 'species']
            if species_taxid:
                species_name = ncbi.get_taxid_translator(species_taxid)[species_taxid[0]]
                count = client.search(taxonomy=species_name)
        
        if count > 0:
            sources = []    
            for strain in client.retrieve():
                info = strain.get("Isolation, sampling and environmental information", {})
                if "taxonmaps" in info:               
                    sources.append({k: v for k, v in info["taxonmaps"].items() if "counts" in k})
            if sources:            
                return dict(functools.reduce(operator.add, map(collections.Counter, sources)))
    except Exception:
        pass
    return sources_none

def get_taxid(accession):
    try:
        search = Entrez.read(Entrez.esearch(db="assembly", term=str(accession)))
        if not search["IdList"]: return None
        summary = Entrez.read(Entrez.esummary(db="assembly", id=search["IdList"][0]))
        return summary['DocumentSummarySet']['DocumentSummary'][0]['Taxid']
    except:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--outdir", required=True)
    parser.add_argument("--chunk_id", type=int, required=True)
    parser.add_argument("--total_chunks", type=int, required=True)
    args = parser.parse_args()

    # Load and split data
    full_df = pd.read_csv(args.input)
    chunks = np.array_split(full_df, args.total_chunks)
    df = chunks[args.chunk_id]

    client = bacdive.BacdiveClient()
    
    # Process TaxIDs
    results = []
    for gid in df["genome_id"]:
        tid = get_taxid(gid)
        habitat = get_habitats(client, tid)
        habitat['genome_id'] = gid
        habitat['taxid'] = tid
        results.append(habitat)
        time.sleep(0.4) # Rate limiting

    # Save individual chunk
    out_path = os.path.join(args.outdir, f"chunk_{args.chunk_id}.csv")
    pd.DataFrame(results).to_csv(out_path, index=False)

if __name__ == "__main__":
    main()
