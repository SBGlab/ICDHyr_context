process HMMSCAN_PFAM {

    tag "${genome}"

    input:
    tuple val(genome), path(faa)
    path pfam_dir

    output:
    tuple val(genome), val("pfam"), path("${genome}.pfam.tbl")

    script:
    """
    hmmscan --cpu ${task.cpus} \
    	--domtblout ${genome}.pfam.tbl \
    	${pfam_dir}/Pfam-A.hmm \
    	${faa}
    """
}
