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

    # Create get_dependencies
    create_get_dependencies(programming_language, folder_path)

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

# Install dependencies
source('install_dependencies.R')

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

# Install dependencies
import install_dependencies
install_dependencies.main()

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

* Install dependencies
do "install_dependencies.do"

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

% Install dependencies
run('install_dependencies.m');

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

* Install dependencies
%include "install_dependencies.sas";

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


# Create get_dependencies()

def create_get_dependencies(programming_language, folder_path):
    """
    Create the install_dependencies script for the specified programming_language.
    
    Parameters:
    programming_language (str): The programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_get_r_dependencies(folder_path)
    elif programming_language.lower() == "python":
        create_get_python_dependencies(folder_path)
    elif programming_language.lower() == "stata":
        create_get_stata_dependencies(folder_path)
    elif programming_language.lower() == "matlab":
        create_get_matlab_dependencies(folder_path)
    elif programming_language.lower() == "sas":
        create_get_sas_dependencies(folder_path)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_get_python_dependencies(folder_path):
    extension = ".py"
    content = """
{% raw %}
import os
import subprocess

def get_dependencies(folder_path=None):
    # If folder_path is not provided, use the folder of the current script
    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))

    # Ensure pipreqs is installed
    try:
        subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', 'pipreqs'])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pipreqs: {e}")
        return

    # Run pipreqs to generate the requirements.txt
    try:
        print(f"Running pipreqs on folder: {folder_path}...")
        subprocess.check_call(['pipreqs', '--force', folder_path])
        print("requirements.txt successfully generated.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate requirements.txt: {e}")
    except FileNotFoundError:
        print("pipreqs not found. Ensure it is installed and accessible.")

# Example usage:
# Replace "path/to/folder" with the path to your Python project folder.
# get_dependencies("path/to/folder")


if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing Python scripts: ")
    get_dependencies(folder_path)
{% endraw %}
"""
    write_script(folder_path, "get_dependencies", extension, content)

def create_get_r_dependencies(folder_path):
    extension = ".R"
    content = """
{% raw %}    
get_dependencies <- function(folder_path = NULL) {
  
  # If folder_path is not provided, use the folder of the current script
  if (is.null(folder_path)) {
    folder_path <- dirname(rstudioapi::getSourceEditorContext()$path)
  }  
  
  # Ensure renv is installed
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  
  # Check if the folder exists
  if (!dir.exists(folder_path)) {
    stop("The specified folder does not exist.")
  }
  
  # List all .R files in the folder
  r_files <- list.files(folder_path, pattern = "\\.R$", full.names = TRUE)
  if (length(r_files) == 0) {
    stop("No .R files found in the specified folder.")
  }
  
  # Detect dependencies using renv
  message("Analyzing dependencies in R scripts...")
  dependencies <- renv::dependencies(path = folder_path)
  
  # Extract relevant columns (package and version)
  dependency_list <- unique(dependencies[, c("Package", "Version")])
  
  # Create a requirements.txt file
  output_file <- file.path(folder_path, "requirements.txt")
  message("Writing dependencies to requirements.txt...")
  
  writeLines(
    paste0(dependency_list$Package, ifelse(!is.na(dependency_list$Version), paste0("==", dependency_list$Version), "")),
    con = output_file
  )
  
  message("requirements.txt successfully generated.")
}

if (interactive()) {
  folder_path <- readline(prompt = "Enter the path to the folder containing R scripts: ")
  get_dependencies(folder_path)
}
{% endraw %}
"""
    
    write_script(folder_path, "get_dependencies", extension, content)

def create_get_stata_dependencies(folder_path):

    extension = ".do"
    content = """
{% raw %}
capture program drop get_dependencies

program define get_dependencies
    * If no folder path is provided, use the folder containing the .do file
    if "`1'" == "" {
        local folder_path = "`c(pwd)'"
    }
    else {
        local folder_path "`1'"
    }

    * Check if folder exists
    if (fileexists("`folder_path'") == 0) {
        di "The specified folder does not exist."
        exit
    }
    
    * Get all .do files in the folder
    local do_files : dir `folder_path' files "*.do"
    
    * Initialize variables to store dependencies
    local datasets ""
    local includes ""
    local packages ""
    
    * Loop through all .do files
    foreach do_file of local do_files {
        * Read the content of the .do file
        file open myfile using "`folder_path'/`do_file'", read
        file read myfile line
        
        * Parse the .do file for dependencies
        while (r(eof) == 0) {
            * Check for dataset dependencies (use command)
            if strpos(line, "use") > 0 {
                local datasets `datasets' `line'
            }
            * Check for included .do files
            if strpos(line, "include") > 0 {
                local includes `includes' `line'
            }
            * Check for package installations
            if strpos(line, "ssc install") > 0 | strpos(line, "net install") > 0 {
                local packages `packages' `line'
            }
            
            * Read next line
            file read myfile line
        }
        file close myfile
    }
    
    * Output detected dependencies
    di "Detected Datasets:"
    di "`datasets'"
    
    di "Detected Included Files:"
    di "`includes'"
    
    di "Detected Package Installations:"
    di "`packages'"
    
    * Optionally, save the results to a text file
    capture file delete "`folder_path'/dependencies.txt"
    file open out using "`folder_path'/dependencies.txt", write
    file write out "Detected Datasets:" _n
    file write out "`datasets'" _n
    file write out "Detected Included Files:" _n
    file write out "`includes'" _n
    file write out "Detected Package Installations:" _n
    file write out "`packages'" _n
    file close out
end
{% endraw %}
"""
    write_script(folder_path, "get_dependencies", extension, content)    

def create_get_matlab_dependencies(folder_path):
    extension = ".m"
    content = """
{% raw %}      
function get_dependencies(folder_path)
    
    % If folder_path is not provided, use the folder of the current script
    if nargin < 1
        folder_path = fileparts(mfilename('fullpath'));
    end

    % Ensure the specified folder exists
    if ~isfolder(folder_path)
        error("The specified folder does not exist.");
    end

    % Find all .m files in the folder
    m_files = dir(fullfile(folder_path, '*.m'));
    if isempty(m_files)
        error("No .m files found in the specified folder.");
    end

    % Initialize a list to store unique dependencies
    unique_files = {};
    unique_products = containers.Map;

    % Analyze each .m file
    for i = 1:length(m_files)
        file_path = fullfile(folder_path, m_files(i).name);
        [required_files, required_products] = matlab.codetools.requiredFilesAndProducts(file_path);

        % Collect required files
        unique_files = unique([unique_files, required_files]);

        % Collect required products (toolboxes)
        for product = required_products
            if ~isKey(unique_products, product.Name)
                unique_products(product.Name) = product.Version;
            end
        end
    end

    % Write dependencies to requirements.txt
    output_file = fullfile(folder_path, 'requirements.txt');
    fid = fopen(output_file, 'w');
    if fid == -1
        error("Unable to create requirements.txt in the specified folder.");
    end

    % Write toolboxes
    fprintf(fid, "MATLAB Toolboxes:\\n");
    product_names = keys(unique_products);
    for i = 1:length(product_names)
        fprintf(fid, "%s==%s\\n", product_names{i}, unique_products(product_names{i}));
    end

    % Write required files
    fprintf(fid, "\\nRequired Files:\\n");
    for i = 1:length(unique_files)
        fprintf(fid, "%s\\n", unique_files{i});
    end

    fclose(fid);
    fprintf("requirements.txt successfully generated in %s.\\n", folder_path);
end
{% endraw %}
"""
    write_script(folder_path, "get_dependencies", extension, content)

def create_get_sas_dependencies(folder_path):
    extension = ".m"
    content = """
{% raw %}     
%macro get_dependencies(folder_path);
    /* Check if folder_path is provided; if not, set it to current working directory */
    %if &folder_path = %then %do;
        %let folder_path = %sysfunc(getoption(work));
        %put NOTE: No folder path provided. Using current working directory: &folder_path;
    %end;

    /* Ensure the folder exists */
    %if %sysfunc(fileexist(&folder_path)) = 0 %then %do;
        %put ERROR: The specified folder does not exist.;
        %return;
    %end;

    /* Get all .sas files in the folder */
    filename dirlist pipe "dir /b &folder_path\\*.sas"; 
    data sas_files;
        infile dirlist truncover;
        input file_name $256.;
    run;

    /* Initialize variables for dependencies */
    %let includes =;
    %let libraries =;

    /* Loop through each .sas file to check for dependencies */
    data _null_;
        set sas_files;
        /* Open the .sas file */
        infile "&folder_path.\\&file_name" length=reclen;
        input line $char256.;

        /* Search for 'include' statements */
        if index(line, 'include') > 0 then do;
            call symputx('includes', cats("&includes ", line));
        end;

        /* Search for 'libname' statements */
        if index(line, 'libname') > 0 then do;
            call symputx('libraries', cats("&libraries ", line));
        end;
    run;

    /* Output detected dependencies */
    %put Detected Include Files:;
    %put &includes;

    %put Detected Library References:;
    %put &libraries;

    /* Optionally save the dependencies to a text file */
    filename outfile "&folder_path.\\dependencies.txt";
    data _null_;
        file outfile;
        put "Detected Include Files:";
        put &includes;
        put "Detected Library References:";
        put &libraries;
    run;

    %put requirements.txt successfully generated at &folder_path.\\dependencies.txt;
%mend get_dependencies;

/* Example usage */
%get_dependencies(C:\\path\\to\\your\\folder);
{% endraw %}
"""
    write_script(folder_path, "get_sas_dependencies", extension, content)


# Create install_dependencies()  # FIX ME - NOT IN USE!!!
def create_install_dependencies(programming_language, folder_path):
    """
    Create the install_dependencies script for the specified programming_language.
    
    Parameters:
    programming_language (str): The programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_install_r_dependencies(folder_path)
    elif programming_language.lower() == "python":
        create_install_python_dependencies(folder_path)
    elif programming_language.lower() == "stata":
        create_install_stata_dependencies(folder_path)
    elif programming_language.lower() == "matlab":
        create_install_matlab_dependencies(folder_path)
    elif programming_language.lower() == "sas":
        create_install_sas_dependencies(folder_path)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_install_python_dependencies(folder_path):
    """
    Creates a script to install required Python dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies.py script will be saved.
    """
    extension = ".py"
    content = """
# Install dependencies for Python

import subprocess
import sys

def main(required_libraries):
    # Get list of installed libraries
    installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

    # Check and install missing libraries
    for lib in required_libraries:
        try:
            # Check if the library is already installed
            if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {lib}: {e}")

if __name__ == "__main__":
    required_libraries = []  # Add more libraries as needed
    main(required_libraries)
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_r_dependencies(folder_path):
    """
    Create the install_dependencies script for R to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".R"
    content = """
# Install R dependencies

# List of required packages
required_packages <- c('tidyr', 'rdrobust', 'ggplot2', 'dplyr')

# Install packages if they are not already installed
for (pkg in required_packages) {
    if (!require(pkg, character.only = TRUE)) {
        install.packages(pkg)
    }
}
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_stata_dependencies(folder_path):
    """
    Create the install_dependencies script for Stata to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".do"
    content = """
* Install Stata dependencies

* List of required packages
ssc install outreg2, replace
ssc install estout, replace
net install rdrobust, from("https://www.example.com/rdrobust"), replace
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_matlab_dependencies(folder_path):
    """
    Create the install_dependencies script for Matlab to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".m"
    content = """
% Install Matlab dependencies

% Example of installing a package (replace with actual package names)
try
    if ~exist('my_package', 'dir')
        disp('Installing my_package...');
        % Assuming the package is on GitHub
        system('git clone https://github.com/username/my_package');
    end
catch
    disp('Error during installation of dependencies');
end
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_sas_dependencies(folder_path):
    """
    Create the install_dependencies script for SAS to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".sas"
    content = """
* Install SAS dependencies;

* List of required packages;
%macro install_dependencies;
    proc fcmp;
        declare object install;
        rc = install.load('SAS/STAT');
        rc = install.load('SAS/GRAPH');
        rc = install.load('SAS/ETS');
    run;
%mend install_dependencies;

* Call the install_dependencies macro;
%install_dependencies;
"""
    write_script(folder_path, "install_dependencies", extension, content)

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
