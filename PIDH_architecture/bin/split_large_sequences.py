#!/usr/bin/env python3

from Bio import SeqIO
import sys

# Maximum sequence length allowed by hmmsearch is ~100K
MAX_SEQ_LEN = 100000
OVERLAP = 5000  # Small overlap to avoid missing boundary hits

def split_sequence(record, max_len, overlap):
    """Split a sequence into overlapping chunks if it exceeds max_len"""
    seq_len = len(record.seq)
    
    if seq_len <= max_len:
        return [record]
    
    chunks = []
    chunk_num = 0
    pos = 0
    
    while pos < seq_len:
        end = min(pos + max_len, seq_len)
        chunk_num += 1
        
        # Create new record for this chunk
        chunk_record = record[pos:end]
        # Append chunk number to the ID to make it unique
        chunk_record.id = f"{record.id}|chunk{chunk_num}"
        chunk_record.description = f"{record.description}|chunk{chunk_num}"
        
        chunks.append(chunk_record)
        
        # Move position by max_len - overlap to create overlapping regions
        pos = end - overlap if (end - overlap) < end else end
        
        # If this was the last chunk, break
        if end == seq_len:
            break
    
    return chunks

# Read input FASTA and split large sequences
input_file = sys.argv[1]
output_file = sys.argv[2]

all_records = []
with open(input_file) as f:
    for record in SeqIO.parse(f, "fasta"):
        chunks = split_sequence(record, MAX_SEQ_LEN, OVERLAP)
        all_records.extend(chunks)

# Write output FASTA
with open(output_file, "w") as f:
    SeqIO.write(all_records, f, "fasta")

print(f"Processed {input_file}: {len(all_records)} sequences (split from input file)")
