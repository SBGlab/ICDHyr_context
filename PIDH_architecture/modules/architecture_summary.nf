process ARCHITECTURE_SUMMARY {

    input:
    tuple val(genome), val(mono_tag), path(mono_file), val(dimer_tag), path(dimer_file)

    output:
    path "*.csv"

    script:
    """
	python3 << EOF
	import pandas as pd
	import random
	import uuid

	genome = "${genome}"
	mono_file = "${mono_file}"
	dimer_file = "${dimer_file}"
	tag = uuid.uuid4().hex  # to avoid filename clashes in parallel runs

	# ---- CONFIG ----
	DELTA = 5.0        # ambiguity threshold (bit score difference)
	EVALUE_CUTOFF = 1e-5

	# ---- PARSERS ----
	def parse_tbl(path, genome_id, is_domtblout=False):
		rows = []

		with open(path) as f:
			for line in f:
				if line.startswith("#"):
					continue

				cols = line.split()

				# Use the protein ID directly from the tblout file (already in format <contig>_<start>_<end>)
				prot_id = cols[0]

				if is_domtblout:
					evalue = float(cols[6])
					bitscore = float(cols[7])

				else:
					evalue = float(cols[4])
					bitscore = float(cols[5])

				if evalue <= EVALUE_CUTOFF:
					rows.append((prot_id, bitscore))

		if not rows:
			return pd.DataFrame(columns=["protein", "bitscore"])

		df = pd.DataFrame(rows, columns=["protein", "bitscore"])

		# keep best hit per protein
		df = df.sort_values("bitscore", ascending=False)\
			.drop_duplicates("protein")

		return df

	mono_df  = parse_tbl(mono_file, genome)
	dimer_df = parse_tbl(dimer_file, genome)

	# rename columns for merge
	mono_df  = mono_df.rename(columns={"bitscore": "mono_score"})
	dimer_df = dimer_df.rename(columns={"bitscore": "dimer_score"})

	# ---- MERGE ----
	df = pd.merge(mono_df, dimer_df, on="protein", how="outer")

	# ---- CLASSIFICATION ----
	def classify(row):
		m = row["mono_score"]
		d = row["dimer_score"]

		if pd.notna(m) and pd.isna(d):
			return "monomeric"
		elif pd.notna(d) and pd.isna(m):
			return "dimeric"
		elif pd.notna(m) and pd.notna(d):
			if abs(m - d) < DELTA:
				return "other"
			return "monomeric" if m > d else "dimeric"
		else:
			return "other"

	df["class"] = df.apply(classify, axis=1)
	df["genome_id"] = [genome]*len(df)

	# ---- OUTPUT ----
	
	df.to_csv(f"{genome}_{tag}.architecture.csv", index=False)
	EOF
    """
}
