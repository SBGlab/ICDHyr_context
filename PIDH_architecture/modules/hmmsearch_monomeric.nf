process HMMSEARCH_MONO {

    tag "${genome}"

    input:
    tuple val(genome), path(faa)
    path hmm

    output:
    tuple val(genome), val("mono"), path("${genome}.mono.tbl")

    script:
    """
    hmmsearch --cpu 1 \
        -E 1e-5 \
        --domE 1e-5 \
        --tblout ${genome}.mono.tbl \
        ${hmm} ${faa}
    """
}
