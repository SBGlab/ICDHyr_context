#!/bin/bash
#SBATCH --job-name=bacdive_para
#SBATCH --output=logs/bacdive_%A_%a.out
#SBATCH --error=logs/bacdive_%A_%a.err
#SBATCH --array=0-9
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00

# --- Configuration ---
INPUT_CSV="/media/alvaro/easystore/work/github/PIDH_architecture/results/final_architecture_summary.csv"
OUT_DIR="./results_chunks"
FINAL_OUTPUT="/media/alvaro/easystore/work/github/PIDH_architecture/results/final_architecture_summary_with_habitat.csv"
TOTAL_CHUNKS=10

mkdir -p $OUT_DIR
mkdir -p logs

# Activate environment
source activate bacdive_env

# --- Step 1: Run the Parallel Chunk ---
python get_bacdive_habitat_parallel.py \
    --input "$INPUT_CSV" \
    --outdir "$OUT_DIR" \
    --chunk_id $SLURM_ARRAY_TASK_ID \
    --total_chunks $TOTAL_CHUNKS

# --- Step 2: Merge the Results ---
# We check if this is the last task in the array
# Note: This only works if all previous tasks finished successfully.
if [ $SLURM_ARRAY_TASK_ID -eq $((TOTAL_CHUNKS - 1)) ]; then
    echo "Last array task detected. Waiting for all chunks to be written..."
    sleep 10 # Buffer to ensure I/O completion across the network file system
    
    python - <<EOF
import pandas as pd
import glob
import os

out_dir = "$OUT_DIR"
final_out = "$FINAL_OUTPUT"

# Find all chunk files
all_files = glob.glob(os.path.join(out_dir, "chunk_*.csv"))

if len(all_files) > 0:
    print(f"Merging {len(all_files)} files...")
    # Read and concatenate
    li = [pd.read_csv(f) for f in all_files]
    df_merged = pd.concat(li, axis=0, ignore_index=True)
    
    # Save final result
    df_merged.to_csv(final_out, index=False)
    print(f"Success! Final file saved to: {final_out}")
    
    # Optional: Clean up chunks
    # for f in all_files: os.remove(f)
else:
    print("No chunk files found to merge.")
EOF
fi
