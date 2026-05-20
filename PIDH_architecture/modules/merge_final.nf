process MERGE_FINAL {

    publishDir "${params.results ?: 'results'}", mode: 'copy'

    input:
    path csvs
    path kingdom_script
    path species_script

    output:
    path "final_architecture_summary.csv"

    script:
    """
    python3 << EOF
    import pandas as pd
    import glob
    import subprocess
    import sys
    from subprocess import PIPE, DEVNULL
    from io import StringIO
    
    # Read all architecture CSV files
    csv_files = glob.glob("*.architecture.csv")
    dfs = [pd.read_csv(f) for f in csv_files]
    
    # Concatenate all dataframes
    grouped_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by genome_id for consistency
    grouped_df = grouped_df.sort_values("genome_id").reset_index(drop=True)
    
    #Add a column indicating predominant architercture type of the genome based on counts
    # For this use the class column of the generated df, which has protein counts for monomeric and dimeric hits.
    
    def determine_architecture(df):
        classification = {}

        for genome_id, group in df.groupby("genome_id"):
            mono_count = len(group[group["class"] == "monomeric"])
            dimer_count = len(group[group["class"] == "dimeric"])

            if mono_count > dimer_count:
                classification[genome_id] = "predominantly_monomeric"

            elif dimer_count > mono_count:
                classification[genome_id] = "predominantly_dimeric"

            else:
                classification[genome_id] = "ambiguous"

        return classification

    grouped_df["genome_predominant_architecture_type"] = grouped_df["genome_id"].map(determine_architecture(grouped_df))

    # Get kingdom mapping from the standalone script
    import os
    env = os.environ.copy()
    env['PROJECT_DIR'] = '${projectDir}'
    result = subprocess.run(['python3', '${kingdom_script}'], 
                           stdout=PIPE, stderr=PIPE, text=True, env=env)
    if result.returncode != 0:
        print(f"Error running kingdom script: {result.stderr}", file=sys.stderr)
    kingdom_df = pd.read_csv(StringIO(result.stdout), sep='\t')
    kingdom_dict = dict(zip(kingdom_df["genome_id"], kingdom_df["kingdom_name"]))
    
    # Add kingdom column
    grouped_df["kingdom"] = grouped_df["genome_id"].map(kingdom_dict).fillna("unknown")

    # Get species mapping from the standalone script
    result = subprocess.run(['python3', '${species_script}'], 
                           stdout=PIPE, stderr=PIPE, text=True, env=env)
    if result.returncode != 0:
        print(f"Error running species script: {result.stderr}", file=sys.stderr)
    species_df = pd.read_csv(StringIO(result.stdout), sep='\t')
    species_dict = dict(zip(species_df["genome_id"], species_df["species_name"]))
    
    # Add specie column
    grouped_df["specie"] = grouped_df["genome_id"].map(species_dict).fillna("unknown")

    # Reorder columns for better readability
    grouped_df = grouped_df[["genome_id", "kingdom", "specie", "protein", "mono_score", "dimer_score", "class", "genome_predominant_architecture_type"]]

    # Save the grouped results
    grouped_df.to_csv("final_architecture_summary.csv", index=False)
    EOF
    """
}
