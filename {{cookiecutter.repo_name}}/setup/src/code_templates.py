import os
import subprocess
import sys
from textwrap import dedent


required_libraries = ['python-dotenv','rpds-py==0.21.0','nbformat'] 
installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

for lib in required_libraries:
    try:
        # Check if the library is already installed
        if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {lib}: {e}")

import nbformat as nbf  # For creating Jupyter notebooks
from dotenv import dotenv_values, load_dotenv


def create_scripts(programming_language, folder_path):
    """
    Creates a project structure with specific scripts for data science tasks
    and a workflow script in R or Python.
    
    Parameters:
    programming_language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the scripts will be saved.
    """
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Script details based on purpose
    scripts = {
        "data_collection": "Data extraction/scraping",
        "preprocessing": "Data cleaning, transformation, feature engineering",
        "modeling": "Training and evaluation of models",
        "utils": "Helper functions or utilities",
        "visualization": "Functions for plots and visualizations"
    }

    # Create the individual step scripts
    for script_name, purpose in scripts.items():
        create_step_script(programming_language, folder_path, script_name, purpose)

    # Create the workflow script that runs all steps
    create_main(programming_language, folder_path)

# Create Step Scripts
def create_step_script(programming_language, folder_path, script_name, purpose):
    """
    Main function to create a step script (R, Python, Stata, Matlab, or SAS) with the necessary structure.
    
    Parameters:
    programming_language (str): Programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the script will be saved.
    script_name (str): The name of the script (e.g., 'data_collection', 'preprocessing').
    purpose (str): The purpose of the script (e.g., 'Data extraction', 'Data cleaning').
    """
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_r_script(folder_path, script_name, purpose)
    elif programming_language.lower() == "python":
        create_python_script(folder_path, script_name, purpose)
    elif programming_language.lower() == "stata":
        create_stata_script(folder_path, script_name, purpose)
    elif programming_language.lower() == "matlab":
        create_matlab_script(folder_path, script_name, purpose)
    elif programming_language.lower() == "sas":
        create_sas_script(folder_path, script_name, purpose)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_r_script(folder_path, script_name, purpose):
    extension = ".R"
    content = f"""
{% raw %}
# {purpose} code

base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
raw_data <- file.path(base_path, "data", "raw")
interim_data <- file.path(base_path, "data", "interrim")
processed_data <- file.path(base_path, "data", "processed")

main <- function() {{
    # {purpose} code
    print('Running {script_name}...')
}}

if (interactive()) {{
    main()
}}
{% endraw %}
"""
    
    write_script(folder_path, script_name, extension, content)

def create_python_script(folder_path, script_name, purpose):
    extension = ".py"
    content = f"""
# {purpose} code

import os
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_data = os.path.join(base_path, "data", "raw")
interim_data = os.path.join(base_path, "data", "interrim")
processed_data = os.path.join(base_path, "data", "processed")

def main():
    # {purpose} code
    print("Running {script_name}...")

if __name__ == "__main__":
    main()
"""
    write_script(folder_path, script_name, extension, content)

def create_stata_script(folder_path, script_name, purpose):
    extension = ".do"
    content = f"""
* {purpose} code

global base_path ".."
global raw_data "$base_path/data/raw"
global interim_data "$base_path/data/interrim"
global processed_data "$base_path/data/processed"

program define {script_name}_main
    display "Running {script_name}..."
end

main
"""
    write_script(folder_path, script_name, extension, content)

def create_matlab_script(folder_path, script_name, purpose):
    extension = ".m"
    content = f"""
% {purpose} code

base_path = fullfile(fileparts(mfilename('fullpath')), '..');
raw_data = fullfile(base_path, 'data', 'raw');
interim_data = fullfile(base_path, 'data', 'interrim');
processed_data = fullfile(base_path, 'data', 'processed');

function {script_name}_main()
    % {purpose} code
    disp('Running {script_name}...');
end

if ~isdeployed
    {script_name}_main();
end
"""
    write_script(folder_path, script_name, extension, content)

def create_sas_script(folder_path, script_name, purpose):
    extension = ".sas"
    content = f"""
* {purpose} code;

%let base_path = ..;
%let raw_data = &base_path./data/raw;
%let interim_data = &base_path./data/interrim;
%let processed_data = &base_path./data/processed;

%macro {script_name}_main();
    %put Running {script_name}...;
%mend {script_name}_main;

%{script_name}_main;
"""
    write_script(folder_path, script_name, extension, content)

def write_script(folder_path, script_name, extension, content):
    """
    Writes the content to a script file in the specified folder path.
    
    Parameters:
    folder_path (str): The folder where the script will be saved.
    script_name (str): The name of the script.
    extension (str): The file extension (e.g., ".py", ".R").
    content (str): The content to be written to the script.
    """
    file_name = f"{script_name}{extension}"
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "w") as file:
        file.write(content)


# Create Main()
def create_main(programming_language, folder_path):
    """
    Main function to create a workflow script that runs all steps in order for the specified programming_language.
    
    Parameters:
    programming_language (str): Programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the workflow script will be saved.
    """
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_r_main(folder_path)
    elif programming_language.lower() == "python":
        create_python_main(folder_path)
    elif programming_language.lower() == "stata":
        create_stata_main(folder_path)
    elif programming_language.lower() == "matlab":
        create_matlab_main(folder_path)
    elif programming_language.lower() == "sas":
        create_sas_main(folder_path)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_r_main(folder_path):
    extension = ".R"
    content = """
# Main: Running all steps in order

# Load Scripts
source('data_collection.R')
source('preprocessing.R')
source('modeling.R')
source('visualization.R')

## Run data collection
data_collection::main()

## Run preprocessing
preprocessing::main()

## Run modeling
modeling::main()

## Run visualization
visualization::main()
"""
    write_script(folder_path, "main", extension, content)

def create_python_main(folder_path):
    extension = ".py"
    content = """
# Main: Running all steps in order

# Load Scripts
import data_collection
import preprocessing
import modeling
import visualization

# Run data collection
data_collection.main()

# Run preprocessing
preprocessing.main()

# Run modeling
modeling.main()

# Run visualization
visualization.main()
"""
    write_script(folder_path, "main", extension, content)

def create_stata_main(folder_path):
    extension = ".do"
    content = """
* Main: Running all steps in order

* Load Scripts
do "data_collection.do"
do "preprocessing.do"
do "modeling.do"
do "visualization.do"

* Run data collection
data_collection_main

* Run preprocessing
preprocessing_main

* Run modeling
modeling_main

* Run visualization
visualization_main
"""
    write_script(folder_path, "main", extension, content)

def create_matlab_main(folder_path):
    extension = ".m"
    content = """
% Main: Running all steps in order

% Run data collection
data_collection_main();

% Run preprocessing
preprocessing_main();

% Run modeling
modeling_main();

% Run visualization
visualization_main();
"""
    write_script(folder_path, "main", extension, content)

def create_sas_main(folder_path):
    extension = ".sas"
    content ="""
* Main: Running all steps in order;

* Load Scripts;
%include "data_collection.sas";
%include "preprocessing.sas";
%include "modeling.sas";
%include "visualization.sas";

* Run data collection;
%data_collection_main;

* Run preprocessing;
%preprocessing_main;

* Run modeling;
%modeling_main;

* Run visualization;
%visualization_main;
"""
    write_script(folder_path, "main", extension, content)


# Create Notebooks
def create_notebooks(programming_language, folder_path):
    """
    Main function to create a notebook for the specified programming_language.
    
    Parameters:
    programming_language (str): The language for which to create the notebook.
    folder_path (str): The directory where the notebook will be saved.
    """
    # Ensure the notebooks folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Call the appropriate function based on the language
    if programming_language.lower() == "python":
        create_python_notebook(folder_path)
    elif programming_language.lower() == "r":
        create_r_notebook(folder_path)
    elif programming_language.lower() == "stata":
        create_stata_notebook(folder_path)
    elif programming_language.lower() == "matlab":
        create_matlab_notebooks(folder_path)
    elif programming_language.lower() == "sas":
        create_sas_notebook(folder_path)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_python_notebook(folder_path):
    file_name = "workflow.ipynb"
    file_path = os.path.join(folder_path, file_name)

    nb = nbf.v4.new_notebook()

    # First cell: Import all scripts
    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
        nbf.v4.new_markdown_cell("### Loading Scripts"),
        nbf.v4.new_code_cell(
            "import sys\n"
            "sys.path.append('src')\n"
            "import data_collection\n"
            "import preprocessing\n"
            "import modeling\n"
            "import visualization\n"
        ),
        nbf.v4.new_markdown_cell("### Run data collection"),
        nbf.v4.new_code_cell("data_collection.main()"),
        nbf.v4.new_markdown_cell("### Run preprocessing"),
        nbf.v4.new_code_cell("preprocessing.main()"),
        nbf.v4.new_markdown_cell("### Run modeling"),
        nbf.v4.new_code_cell("modeling.main()"),
        nbf.v4.new_markdown_cell("### Run visualization"),
        nbf.v4.new_code_cell("visualization.main()")
    ]
    nb.cells.extend(cells)

    # Write the notebook to a file
    with open(file_path, "w") as f:
        nbf.write(nb, f)

def create_r_notebook(folder_path):
    file_name = "workflow.Rmd"
    file_path = os.path.join(folder_path, file_name)

    # Create RMarkdown content with the requested structure
    content = dedent("""{% raw %}
    ---
    title: "Workflow: Running all steps in order"
    output: html_document
    ---

    # Workflow

    ## Load Scripts
    ```{r}             
    source("src/data_collection.R")
    source("src/preprocessing.R")
    source("src/modeling.R")
    source("src/visualization.R")
    ```
    ## Run data collection
    ```{r}
    data_collection::main()
    ```
    ## Run preprocessing
    ```{r}
    preprocessing::main()
    ```
    ## Run modeling
    ```{r}
    modeling::main()
    ```
    ## Run visualization
    ```{r}
    visualization::main()
    ```
    {% endraw %}""")

    # Write the RMarkdown content to a file
    with open(file_path, "w") as file:
        file.write(content)

def create_stata_notebook(folder_path):
    file_name = "workflow.ipynb"
    file_path = os.path.join(folder_path, file_name)
    
    nb = nbf.v4.new_notebook()

    # First cell: Configure Stata setup
    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
        nbf.v4.new_markdown_cell("### Stata Setup"),
        nbf.v4.new_code_cell(
            "import stata_setup\n"
            "stata_setup.config('/work/stata17', 'se')\n"
        ),
        nbf.v4.new_markdown_cell("### Run data collection"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do src/data_collection.do\n"
                             "data_collection_main()"),
        nbf.v4.new_markdown_cell("### Run preprocessing"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do src/preprocessing.do\n"
                             "preprocessing_main()"),
        nbf.v4.new_markdown_cell("### Run modeling"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do src/modeling.do\n"
                             "modeling_main()"),
        nbf.v4.new_markdown_cell("### Run visualization"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do src/visualization.do\n"
                             "visualization_main()")
    ]
    nb.cells.extend(cells)

    # Write the notebook to a file
    with open(file_path, "w") as f:
        nbf.write(nb, f)

def create_matlab_notebooks(folder_path):
    # Create MATLAB notebook (.mlx) and Jupyter notebook
    mlx_file_name = "workflow.mlx"
    mlx_file_path = os.path.join(folder_path, mlx_file_name)
    
    # Create Jupyter notebook using jupyter-matlab-proxy
    ipynb_file_name = "workflow.ipynb"
    ipynb_file_path = os.path.join(folder_path, ipynb_file_name)

    nb = nbf.v4.new_notebook()

    # First cell: Load necessary paths and scripts (without running functions)
    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
        nbf.v4.new_markdown_cell("### MATLAB Setup (using jupyter-matlab-proxy)"),
        nbf.v4.new_code_cell(
            "%%matlab\n"
            "addpath('src')\n"
        ),
        nbf.v4.new_markdown_cell("### Run data collection"),
        nbf.v4.new_code_cell("data_collection_main()"),
        nbf.v4.new_markdown_cell("### Run preprocessing"),
        nbf.v4.new_code_cell("preprocessing_main()"),
        nbf.v4.new_markdown_cell("### Run modeling"),
        nbf.v4.new_code_cell("modeling_main()"),
        nbf.v4.new_markdown_cell("### Run visualization"),
        nbf.v4.new_code_cell("visualization_main()")
    ]
    nb.cells.extend(cells)

    # Write the Jupyter notebook to a file
    with open(ipynb_file_path, "w") as f:
        nbf.write(nb, f)

    # For .mlx file, write MATLAB-specific workflow
    mlx_content = dedent("""%% Workflow: Running all steps in order
    % MATLAB Setup
    addpath('src')

    %% Run data collection
    data_collection_main()

    %% Run preprocessing
    preprocessing_main()

    %% Run modeling
    modeling_main()

    %% Run visualization
    visualization_main()
    """)

    with open(mlx_file_path, "w") as f:
        f.write(mlx_content)

def create_sas_notebook(folder_path):
    file_name = "workflow.ipynb"
    file_path = os.path.join(folder_path, file_name)
    
    nb = nbf.v4.new_notebook()

    # First cell: Configure SAS setup for Jupyter (without running functions)
    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running all steps in order"),
        nbf.v4.new_markdown_cell("### SAS Setup (using sas_kernel)"),
        nbf.v4.new_code_cell(
            "import saspy\n"
            "sas = saspy.SASsession()\n"
        ),
        nbf.v4.new_markdown_cell("### Run data collection"),
        nbf.v4.new_code_cell("sas.submit('data_collection_main.sas')"),
        nbf.v4.new_markdown_cell("### Run preprocessing"),
        nbf.v4.new_code_cell("sas.submit('preprocessing_main.sas')"),
        nbf.v4.new_markdown_cell("### Run modeling"),
        nbf.v4.new_code_cell("sas.submit('modeling_main.sas')"),
        nbf.v4.new_markdown_cell("### Run visualization"),
        nbf.v4.new_code_cell("sas.submit('visualization_main.sas')")
    ]
    nb.cells.extend(cells)

    # Write the notebook to a file
    with open(file_path, "w") as f:
        nbf.write(nb, f)
