
from Bio import Entrez
import xml.etree.ElementTree as ET
import pandas as pd
import time

Entrez.email = "agargantilla@cnb.csic.es"

def get_habitat_comprehensive(accession):
    print(f"Processing {accession}...")
    try:
        # Step 1: Bridge via Assembly database
        search_results = Entrez.read(Entrez.esearch(db="assembly", term=accession))
        if not search_results["IdList"]:
            return "No Assembly found."
        
        summary = Entrez.read(Entrez.esummary(db="assembly", id=search_results["IdList"][0]))
        biosample_id = summary['DocumentSummarySet']['DocumentSummary'][0]['BioSampleId']
        
        # Step 2: Fetch BioSample XML
        time.sleep(0.4) # Respect rate limits
        handle = Entrez.efetch(db="biosample", id=biosample_id, retmode="xml")
        root = ET.fromstring(handle.read())
        handle.close()
        
        # Step 3: Map all attributes into a dictionary
        metadata = {
            (attr.get("harmonized_name") or attr.get("attribute_name")).lower(): attr.text 
            for attr in root.findall(".//Attribute")
        }
        print(metadata)
        direct_habitat = None
        taxid_habitat = None
        host_info = None
        description_text = None

        # Step 4: Define potential keys in order of relevance
        # 1. Direct Environmental Keys
        habitat_keys = [
            "habitat", 
            "isolation_source", 
            "env_biome",
            "env_medium",
            "env_feature", 
            "env_material",
            "env_broad_scale",
            "env_local_scale"
            "host",
            "host_habitat",
            "geo_loc_name",
            "body_site"
        ]
        direct_habitat = {k: metadata[k] for k in habitat_keys if k in metadata}
        print(f"Direct habitat keys found: {direct_habitat}")

        if len(direct_habitat.keys()) == 0:   
            # 2. Get TaxID from the assembly summary
            taxid = summary['DocumentSummarySet']['DocumentSummary'][0]['Taxid']
            print(f"TaxID: {taxid}")
            tax_handle = Entrez.efetch(db="taxonomy", id=taxid, retmode="xml")
            tax_data = Entrez.read(tax_handle)  # Bio.Entrez handles the list/dict structure here
            print(tax_data)
            tax_handle.close()

            if tax_data is not None and len(tax_data) > 0:
                # Taxonomy results are always a list
                properties = tax_data[0].get("Properties", [])
                for prop in properties:
                    print(f"Taxonomy property: {prop.get('Property')} = {prop.get('Value')}")
                    if prop.get("Property") == "habitat":
                        return f"Habitat (Taxonomy): {prop.get('Value')}"

        if taxid_habitat is not None or len(taxid_habitat) == 0:
            # 3. Host/Clinical Keys (common in V. cholerae clinical isolates)
            host_keys = [
                "host", 
                "host_habitat", 
                "host_disease", 
                "host_health_state", 
                "host_age", 
                "host",
                "body_site"
            ]
            
            # Extract matches
            host_info = {k: metadata[k] for k in host_keys if k in metadata}
            print(f"Host-associated keys found: {host_info}")

        if host_info is not None and len(host_info.keys()) == 0:
            print("test")
            if len(host_info.keys()) == 0:
                # 4. Fallback: Search the Description and Title fields
                # These often contain text like "isolated from stool" or "environmental isolate"
                description_node = root.find(".//Description/Title")

                if description_node is not None:
                    description_text = description_node.text

                else:
                    description_text = "No description available."

                print(f"Description text: {description_text}")
        
        # Logic to return the best available info
        if direct_habitat:
            found_data = direct_habitat

        elif host_info:
            found_data = host_info

        elif description_text is not None:
            found_data = description_text

        else:
            print("No habitat data found in structured or text fields.")
            found_data = None

        return found_data if found_data else "NF"

    except Exception as e:
        return f"Error: {str(e)}"

from Bio import Entrez

def get_habitat_final_resort(accession):
    # ... [Keep your existing BioSample logic here] ...
    
    # If BioSample only gives you the species name (like your result), 
    # query the Taxonomy database for the species' general habitat.
    try:
        # Get TaxID from the assembly summary
        taxid = summary['DocumentSummarySet']['DocumentSummary']['Taxid']
        
        tax_handle = Entrez.efetch(db="taxonomy", id=taxid, retmode="xml")
        tax_root = ET.fromstring(tax_handle.read())
        
        # Look for the 'Comments' or 'Properties' section
        # For Vibrio, this often mentions "marine" or "aquatic"
        properties = tax_root.find(".//Property/Value")
        if properties is not None:
            return f"General Habitat: {properties.text}"
            
    except:
        pass
    
    return "Habitat information is not digitally encoded for this legacy record."

# Example usage
source_df = pd.read_csv("results/final_architecture_summary.csv", nrows=20)
genome_ids = source_df["genome_id"].unique().tolist()
habitat = {genome_id: get_habitat_comprehensive(genome_id) for genome_id in genome_ids}

source_df["Habitat"] = source_df["genome_id"].map(habitat)
source_df.to_csv("results/final_architecture_summary_with_habitat.csv", index=False)
