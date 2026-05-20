process SPLIT_LARGE_SEQUENCES {

    tag "${genome}"

    input:
    tuple val(genome), path(faa)
    path split_script

    output:
    tuple val(genome), path("${genome}_split.faa")

    script:
    """
    python3 ${split_script} ${faa} ${genome}_split.faa
    """
}
