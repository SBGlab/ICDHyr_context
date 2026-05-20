import argparse
import pandas as pd
import collections
import functools
import operator
import time
import bacdive
from ete3 import NCBITaxa
from Bio import Entrez

# Initialize tools
ncbi = NCBITaxa()
Entrez.email = "agargantilla@cnb.csic.es"

def get_habitats(client, taxid):
    sources_none = {
        'soil counts': None,
        'aquatic counts': None,
        'animal counts': None,
        'plant counts': None
    }
    
    if not taxid or str(taxid) == "None" or str(taxid) == "nan":
        return sources_none
        	  	
    # 1. Search by specific NCBI TaxID
    try:
        count = client.search(taxonomy=str(taxid))
    except Exception as e:
        print(f"BacDive API error for {taxid}: {e}")
        return sources_none
    
    # 2. Fallback to Species name
    if count == 0:
        try:
            lineage = ncbi.get_lineage(taxid)
            ranks = ncbi.get_rank(lineage)
            species_taxid = [tid for tid, rank in ranks.items() if rank == 'species']
            if species_taxid:
                species_name = ncbi.get_taxid_translator(species_taxid)[species_taxid[0]]
                count = client.search(taxonomy=species_name)
        except Exception:
            return sources_none

    # 3. Retrieve data
    if count > 0:
        sources = []    
        for strain in client.retrieve():
            entry_habitat_info = strain.get("Isolation, sampling and environmental information", {})
            if "taxonmaps" in entry_habitat_info:               
                sources.append({k: v for k, v in entry_habitat_info["taxonmaps"].items() if "counts" in k})
                    
        if sources:            
            return dict(functools.reduce(operator.add, map(collections.Counter, sources)))
    
    return sources_none
    
def get_taxid(accession):
    try:
        search_results = Entrez.read(Entrez.esearch(db="assembly", term=str(accession)))
        if not search_results["IdList"]:
            return None
        summary = Entrez.read(Entrez.esummary(db="assembly", id=search_results["IdList"][0]))
        return summary['DocumentSummarySet']['DocumentSummary'][0]['Taxid']
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch BacDive habitat data for genome accessions.")
    parser.add_argument("-i", "--input", required=True, help="Path to input CSV")
    parser.add_argument("-o", "--output", required=True, help="Path to output CSV")
    args = parser.parse_args()

    # It's better to init client inside main for scope
    client = bacdive.BacdiveClient()

    df = pd.read_csv(args.input)
    
    print(f"Processing {len(df)} records...")
    
    # 1. Get unique TaxIDs to save API calls
    genome_ids = df["genome_id"].unique().tolist()
    taxid_map = {}
    for gid in genome_ids:
        taxid_map[gid] = get_taxid(gid)
        time.sleep(0.34) # Respect NCBI rate limits (3 requests/sec)

    df["taxid"] = df["genome_id"].map(taxid_map)

    # 2. Get habitats
    habitat_data = []
    for tid in df["taxid"]:
        habitat_data.append(get_habitats(client, tid))
        # Optional: time.sleep(0.1) if BacDive rate limits are hit

    habitat_df = pd.DataFrame(habitat_data)
    
    # 3. Finalize
    final_df = pd.concat([df.reset_index(drop=True), habitat_df], axis=1)
    final_df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
