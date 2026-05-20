nextflow.enable.dsl=2

include { HMMSEARCH_MONO } from './modules/hmmsearch_monomeric.nf'
include { HMMSEARCH_DIMER }   from './modules/hmmsearch_dimeric.nf'
include { HMMSCAN_PFAM }      from './modules/hmmscan_pfam.nf'
include { ARCHITECTURE_SUMMARY }           from './modules/architecture_summary.nf'
include { PROCESS_FASTA }        from './modules/process_fasta.nf'
include { MERGE_FINAL } from './modules/merge_final.nf'
include { SPLIT_LARGE_SEQUENCES } from './modules/split_large_sequences.nf'

params.chunks    = "chunks/*.faa"
params.hmm_mono  = "resources/idh_monomeric.hmm"
params.hmm_dimer = "resources/idh_dimeric.hmm"
params.pfam_db = "resources/pfam/"
params.results = "results"

workflow {

    /*
     * INPUT: raw chunks
     */
    chunks_ch = Channel.fromPath(params.chunks, checkIfExists: true)

    /*
     * STEP 1: split into (genome, faa)
     */
    genomes_ch = PROCESS_FASTA(chunks_ch)
    	.flatten()
    	.map { file -> tuple(file.baseName, file) }

    /*
     * STEP 2: split large sequences (hmmsearch has 100K limit)
     */
    split_ch = SPLIT_LARGE_SEQUENCES(genomes_ch, file("${projectDir}/bin/split_large_sequences.py"))
    
    // 🔥 DUPLICATE CHANNEL SAFELY for both searches
    ch1 = split_ch
    ch2 = split_ch

    /*
     * DEBUG (optional but strongly recommended)
     */

    /*
     * STEP 3: HMM searches (1 genome = 1 task)
     */
    mono_hits  = HMMSEARCH_MONO(ch1, file(params.hmm_mono))
    dimer_hits = HMMSEARCH_DIMER(ch2, file(params.hmm_dimer))

    /*
     * STEP 4: combine results per genome
     * (IMPORTANT: must still preserve tuple structure)
     */
    paired = mono_hits
    	.join(dimer_hits)
        
    /*
     * STEP 5: classification
     */
    summary = ARCHITECTURE_SUMMARY(paired)
    /*
     * STEP 6: merge with taxonomy and output final CSVs
     */
    MERGE_FINAL(summary.collect(), 
                file("${projectDir}/bin/map_genome_to_kingdom.py"),
                file("${projectDir}/bin/map_genome_to_species.py"))
}
