process HMMSEARCH_DIMER {

    tag "${genome}"

    input:
    tuple val(genome), path(faa)
    path hmm

    output:
    tuple val(genome), val("dimer"), path("${genome}.dimer.tbl")

    script:
    """
    hmmsearch --cpu 1 \
        -E 1e-5 \
        --domE 1e-5 \
        --tblout ${genome}.dimer.tbl \
        ${hmm} ${faa}
    """
}
