#!/usr/bin/env bash

set -euo pipefail

############################
# CONFIGURATION
############################

OUTDIR="idh_seed_pipeline"
THREADS=8

mkdir -p ${OUTDIR}/{raw,filtered,clustered,aligned,hmm,logs}
cd ${OUTDIR}

############################
# FUNCTIONS
############################

download_uniprot() {
    QUERY="$1"
    OUTFILE="$2"

    echo "Downloading: $OUTFILE"

    curl -sG "https://rest.uniprot.org/uniprotkb/stream" \
        --data-urlencode "query=${QUERY}" \
        --data-urlencode "format=fasta" \
        -o "${OUTFILE}"

    # sanity check
    if [[ ! -s "${OUTFILE}" ]]; then
        echo "ERROR: Download failed or empty file: ${OUTFILE}"
        exit 1
    fi
}

filter_by_length() {
    INFILE="$1"
    OUTFILE="$2"
    MINLEN="$3"
    MAXLEN="$4"

    seqkit seq -m ${MINLEN} -M ${MAXLEN} ${INFILE} > ${OUTFILE}
}

############################
# STEP 1 — DOWNLOAD SEQUENCES
############################

echo "=== Step 1: Downloading UniProt sequences ==="

# Dimeric (~400 aa)
QUERY_DIMERIC='(protein_name:"isocitrate dehydrogenase" OR gene:icd) AND (taxonomy_id:2 OR taxonomy_id:2157) AND fragment:false NOT protein_name:"isopropylmalate dehydrogenase"'

download_uniprot "${QUERY_DIMERIC}" "raw/dimeric_raw.fasta"

# Monomeric (~800 aa)
QUERY_MONOMERIC="${QUERY_DIMERIC}"

download_uniprot "${QUERY_MONOMERIC}" "raw/monomeric_raw.fasta"

############################
# STEP 2 — LENGTH FILTERING
############################

echo "=== Step 2: Length filtering ==="

# Dimeric: 350–550 aa
filter_by_length "raw/dimeric_raw.fasta" "filtered/dimeric.fasta" 350 550

# Monomeric: 650–1000 aa
filter_by_length "raw/monomeric_raw.fasta" "filtered/monomeric.fasta" 650 1000

############################
# STEP 3 — REMOVE REDUNDANCY
############################

echo "=== Step 3: Clustering (CD-HIT) ==="

cd-hit -i filtered/dimeric.fasta -o clustered/dimeric_nr.fasta -c 0.9 -n 5 -T ${THREADS}
cd-hit -i filtered/monomeric.fasta -o clustered/monomeric_nr.fasta -c 0.9 -n 5 -T ${THREADS}

############################
# STEP 4 — MULTIPLE ALIGNMENT
############################

echo "=== Step 4: Alignment (MAFFT) ==="

mafft --auto --thread ${THREADS} clustered/dimeric_nr.fasta > aligned/dimeric.aln
mafft --auto --thread ${THREADS} clustered/monomeric_nr.fasta > aligned/monomeric.aln

############################
# STEP 5 — BUILD HMMs
############################

echo "=== Step 5: HMM construction ==="

hmmbuild hmm/idh_dimeric.hmm aligned/dimeric.aln
hmmbuild hmm/idh_monomeric.hmm aligned/monomeric.aln

############################
# STEP 6 — REPORT
############################

echo "=== Step 6: Summary ==="

echo "Dimeric sequences:"
seqkit stats filtered/dimeric.fasta

echo "Monomeric sequences:"
seqkit stats filtered/monomeric.fasta

echo "Clustered (non-redundant):"
seqkit stats clustered/dimeric_nr.fasta
seqkit stats clustered/monomeric_nr.fasta

echo "HMMs generated in:"
echo "  hmm/idh_dimeric.hmm"
echo "  hmm/idh_monomeric.hmm"

echo "=== DONE ==="
