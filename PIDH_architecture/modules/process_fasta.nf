process PROCESS_FASTA {

    input:
    path chunk

    output:
    path "*.faa"

    script:
    """
    python3 << EOF
from Bio import SeqIO
import re

def get_genome(rid):
    m = re.match(r"^(GCA_[0-9]+\\.[0-9]+)", rid)
    return m.group(1) if m else None

def get_contig(rid):
    # Extract contig from header like: GCA_000005825.2_CP001878.2_1
    # Format is: GCA_<version>_<contig>_<index>
    parts = rid.split("_")
    if len(parts) >= 3:
        return parts[2]
    return None

#function to get start and end positions of proteins in the fasta file.
#headers are in the format: 
#   GCA_000005825.2_CP001878.2_1 # 816 # 2168 # 1 # ID=1_1;partial=00;start_type=TTG;rbs_motif=AGGAGG;rbs_spacer=5-10bp;gc_cont=0.382
#   <genome>_<contig>_<idx> # <start> # <end> # <strand> # <other info>
def get_protein_positions(rid):
    parts = rid.split("#")
    if len(parts) < 4:
        return None, None
    try:
        start = int(parts[1].strip())
        end = int(parts[2].strip())
        return start, end
        
    except ValueError:
        return None, None

def generate_protein_id(rid):
    # Generate protein ID as <contig>_<start>_<end>
    contig = get_contig(rid)
    start, end = get_protein_positions(rid)
    
    if contig and start is not None and end is not None:
        return f"{contig}_{start}_{end}"
    return None

seqs = {}

for record in SeqIO.parse("${chunk}", "fasta"):
    genome = get_genome(record.id)
    if genome:
        # Combine ID and description to get full header for position parsing
        full_header = f"{record.id} {record.description}"
        new_protein_id = generate_protein_id(full_header)
        if new_protein_id:
            # Create new record with modified ID
            record.id = new_protein_id
            record.description = ""  # Clear description to have clean header
            seqs.setdefault(genome, []).append(record)

for genome, records in seqs.items():
    # Write FASTA file
    fname = f"{genome}.faa"
    with open(fname, "w") as f:
        for r in records:
            f.write(f">{r.id}\\n{r.seq}\\n")
EOF
    """
}
