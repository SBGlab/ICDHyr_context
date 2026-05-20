Here is a **clean README-style summary** of the **final synchronized Nextflow + HMM + Pfam pipeline** you built.

---

# 🧬 IDH Architecture Classification Pipeline (Nextflow DSL2)

## Overview

This pipeline performs large-scale classification of prokaryotic isocitrate dehydrogenase (IDH) enzymes into:

* **Monomeric**
* **Dimeric**
* **Other**

It integrates:

* HMMER (monomeric + dimeric IDH profiles)
* Pfam domain validation
* genome-aware parsing
* per-genome percentage summarization
* scalable execution for ~40,000 genomes

---

# 📊 Pipeline Summary

## Input

* Multi-FASTA protein dataset with headers:

  ```
  GCA_000005825.2_CP001878.2_1
  ```

  where:

  * Genome ID = `GCA_000005825.2`
  * Protein ID = `CP001878.2_1`

---

## Output

For each genome:

### 1. Protein-level table

```
genome.proteins.tsv
```

| genome | protein | architecture | length | mono_score | dimer_score |

---

### 2. Genome-level summary

```
genome.summary.tsv
```

| genome | total | monomeric_pct | dimeric_pct | other_pct |

---

# ⚙️ Pipeline Steps

---

## 1. Chunking (preprocessing)

External step using `seqkit`:

```bash
seqkit split2 -s 50000 -O chunks all_proteins.faa
```

Produces:

```
chunks/
├── part_001.faa
├── part_002.faa
```

---

## 2. Load chunks into Nextflow

```groovy
Channel.fromPath("chunks/*.faa")
```

Optional test mode:

```groovy
.take(5)
```

---

## 3. SPLIT_FASTA (genome extraction)

Each chunk is processed in parallel.

### Function:

Extract genome ID from headers:

```text
GCA_000005825.2_CP001878.2_1 → GCA_000005825.2
```

### Output:

Per-genome FASTA files:

```
split_chunkX/
├── GCA_000005825.2.faa
├── GCA_000123456.1.faa
```

---

## 4. MERGE_GENOMES (safety step)

Combines fragmented genome files across chunks:

* prevents split artifacts
* ensures one FASTA per genome

---

## 5. HMMER search

### Monomeric IDH:

```bash
hmmsearch idh_monomeric.hmm
```

### Dimeric IDH:

```bash
hmmsearch idh_dimeric.hmm
```

Outputs:

```
genome.mono.tbl
genome.dimer.tbl
```

---

## 6. Pfam validation

```bash
hmmscan Pfam-A.hmm
```

Ensures IDH domain presence:

```
PF00180
```

Filters false positives and domain fusions.

---

## 7. Classification (Python)

Combines:

* monomeric score
* dimeric score
* Pfam domains
* sequence length

### Rules:

* higher HMM score wins
* length sanity check:

  * monomeric ≥ 650 aa
  * dimeric 350–550 aa
* must contain PF00180 domain

---

## 8. Genome summary aggregation

For each genome:

```
monomeric_pct = count / total * 100
dimeric_pct   = count / total * 100
other_pct     = count / total * 100
```

---

# 🧠 Key Design Features

## ✔ Genome-aware parsing

Uses regex-based extraction:

```
GCA_[0-9]+\.[0-9]+
```

## ✔ Fully parallel execution

* chunk-level parallelism
* genome-level parallelism
* HMMER parallelization per genome

## ✔ Scalable architecture

Designed for:

* 40,000+ genomes
* millions of proteins

## ✔ Biological validation layers

* HMM competition (monomer vs dimer)
* Pfam domain confirmation
* length constraints

---

# 🚀 Expected usage

```bash
nextflow run main.nf \
  --chunks "chunks/*.faa" \
  --hmm_mono resources/idh_monomeric.hmm \
  --hmm_dimer resources/idh_dimeric.hmm \
  --pfam_db resources/Pfam-A.hmm
```

---

# 📌 Final Output Use Cases

* phylogenetic annotation (iTOL)
* evolutionary distribution of IDH architectures
* genome-wide enzyme structure mapping
* comparative prokaryotic metabolism studies

---
