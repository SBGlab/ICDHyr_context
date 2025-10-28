This directory contains the code and notebooks used to run simulations, analyze results, and generate figures for the paper "Functional redundancy driven by isocitrate dehydrogenase enhance metabolic robustness in Pseudomonas putida KT2440 providing flexible flux control in TCA".

Dependencies

Recommended base:
- Python 3.8 or newer (3.9/3.10/3.11 recommended)
- Conda (miniconda or anaconda) is recommended for environment management

Common Python packages used by the scripts and notebooks (install via pip or conda):
- numpy
- pandas
- scipy
- matplotlib
- seaborn
- scikit-learn
- jupyterlab or notebook
- cobra (COBRApy)    # for constraint-based metabolic modeling
- optlang             # solver interface used by COBRApy
- python-libsbml or libsbml (if SBML files are parsed)
- tqdm                # progress bars
- networkx            # network analysis / graph utilities

Optional / domain-specific tools (install if needed):
- escher              # pathway visualization
- cameo               # strain design and flux analysis helpers
- gurobi or cplex     # commercial solvers (if used); otherwise use glpk or scip via optlang

R (optional):
- R >= 4.0
- tidyverse, ggplot2, data.table (if any R scripts are present)

Installation examples

1) Using conda (recommended):

- Create a new environment:
  conda create -n icdhyr python=3.10 -y
  conda activate icdhyr

- Install common packages via conda and pip (example):
  conda install -c conda-forge numpy pandas scipy matplotlib seaborn scikit-learn jupyterlab networkx tqdm -y
  conda install -c conda-forge cobra optlang -y
  pip install escher python-libsbml cameo

2) Using pip into an existing environment:
  python -m pip install --upgrade pip
  pip install numpy pandas scipy matplotlib seaborn scikit-learn jupyterlab cobra optlang python-libsbml tqdm networkx

Notes on solvers

- COBRApy requires a linear programming solver. Install a solver supported by optlang (e.g., glpk, scip, gurobi, cplex). If a commercial solver (Gurobi/CPLEX) is used for some analyses, you will need appropriate licenses and to configure the solver according to its documentation.

Running analyses

- Many of the scripts assume data are present under ../data/ and will write outputs to ../results/ or ../figs/. Check individual script headers for specific input/output expectations.
- Notebooks can be launched with jupyterlab or jupyter notebook and executed interactively or with nbconvert.

Reproducibility tips

- Check each script or notebook header for a list of required packages and exact versions. If a requirements.txt or environment.yml is provided in this repository (or will be added), prefer using that to reproduce the exact environment.
- If analyses are computationally heavy, intermediate files may be included in data/ or results/.

Contact

If you encounter issues installing dependencies or running scripts, please open an issue in this repository describing your environment and the error messages.
