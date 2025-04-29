import os
from textwrap import dedent
import pathlib

from .general_tools import *

pip_installer(required_libraries = ['rpds-py==0.21.0','nbformat'] )

import nbformat as nbf  # For creating Jupyter notebooks


def write_script(folder_path, script_name, extension, content):
    """
    Writes the content to a script file in the specified folder path.
    
    Parameters:
    folder_path (str): The folder where the script will be saved.
    script_name (str): The name of the script.
    extension (str): The file extension (e.g., ".py", ".R").
    content (str): The content to be written to the script.
    """
    # Create the folder if it doesn't exist
    full_folder_path = pathlib.Path(__file__).resolve().parent.parent.parent / folder_path
    full_folder_path.mkdir(parents=True, exist_ok=True)


    file_name = f"{script_name}{extension}"
    file_path = os.path.join(folder_path, file_name)

        # Ensure the notebooks folder exists

    file_path= str(pathlib.Path(__file__).resolve().parent.parent.parent /  pathlib.Path(file_path))

    with open(file_path, "w") as file:
        if isinstance(content,str):
            file.write(content)
        else:
            nbf.write(content, file)


def create_scripts(programming_language, folder_path):
    """
    Creates a project structure with specific scripts for data science tasks
    and a workflow script in R or Python.
    
    Parameters:
    programming_language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the scripts will be saved.
    """

    if programming_language.lower() not in ["python","r","matlab","stata","sas"]:
        return
    
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

    # Create Install_dependencies
    create_install_dependencies(programming_language, folder_path)

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
import sys
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_data = os.path.join(base_path, "data", "raw")
interim_data = os.path.join(base_path, "data", "interrim")
processed_data = os.path.join(base_path, "data", "processed")
setup_path = os.path.join(base_path, "setup") 
sys.path.append(setup_path)
from utils import *

@ensure_correct_kernel
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

# Create Main()
def create_main(programming_language, folder_path):
    """
    Main function to create a workflow script that runs all steps in order for the specified programming_language.
    
    Parameters:
    programming_language (str): Programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the workflow script will be saved.
    """
 
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
    content = r"""
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
    content = r"""
# Main: Running all steps in order

import os
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
setup_path  os.path.join(base_path, "setup") 
sys.path.append(setup_path)
from utils import *

@ensure_correct_kernel
def main():
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

if __name__ == "__main__":
    main()
"""
    write_script(folder_path, "main", extension, content)

def create_stata_main(folder_path):
    extension = ".do"
    content = r"""
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
    content = r"""
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
    content =r"""
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
    content = r"""
{% raw %}
import os
import subprocess
import ast
import sys
import sysconfig
from datetime import datetime
import importlib

import yaml
from typing import Dict, List
import pathlib

# Ensure the project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils import *

def resolve_parent_module(module_name):
    if '.' in module_name:
        return module_name.split('.')[0]
    return module_name

def get_setup_dependencies(folder_path: str = None, file_name: str = "dependencies.txt"):
    
    def get_dependencies_from_file(python_files):
        used_packages = set()

        for file in python_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_packages.add(resolve_parent_module(alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        used_packages.add(resolve_parent_module(node.module))
            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Skipping {file} due to parse error: {e}")
        
        # List Python standard library modules by checking files in the standard library path
        std_lib_path = sysconfig.get_paths()["stdlib"]
        standard_libs = []
        for root, dirs, files in os.walk(std_lib_path):
            for file in files:
                if file.endswith(".py") or file.endswith(".pyc"):
                    standard_libs.append(os.path.splitext(file)[0])

        installed_packages = {}
        for package in used_packages:
            try:
                version = importlib.metadata.version(package)
                installed_packages[package] = version
            except importlib.metadata.PackageNotFoundError:
                if package not in standard_libs and package not in sys.builtin_module_names:
                    installed_packages[package] = "Not available" 
        
        python_script_names = {os.path.splitext(os.path.basename(file))[0] for file in python_files}
        valid_packages = {package: version for package, version in installed_packages.items()
                        if not (version == "Not available" and package in python_script_names)}
        return valid_packages
    
    def process_requirements(requirements_file: str) -> Dict[str, str]:
        
        def extract_conda_dependencies(env_data: dict) -> List[str]:
            packages = []
            for item in env_data.get('dependencies', []):
                if isinstance(item, str):
                    packages.append(item.split("=")[0])  # Extract package name before "="
                elif isinstance(item, dict) and 'pip' in item:
                    packages.extend([pkg.split("==")[0] for pkg in item['pip'] if isinstance(pkg, str)])
            return packages

        print(f"Processing requirements from: {requirements_file}")
        installed_packages = {}
        try:
            if requirements_file.endswith(".txt"):
                with open(requirements_file, "r") as f:
                    packages = [line.split("==")[0].strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
            elif requirements_file.endswith((".yml", ".yaml")):
                with open(requirements_file, "r") as f:
                    env_data = yaml.safe_load(f)
                    packages = extract_conda_dependencies(env_data)

            for package in packages:
                try:
                    version = importlib.metadata.version(package)
                    installed_packages[package] = version
                except importlib.metadata.PackageNotFoundError:
                    installed_packages[package] = "Not available"
        except Exception as e:
            print(f"Error processing requirements file: {e}")
        return installed_packages

    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Scanning folder: {folder_path}")
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified folder.")
        return

    installed_packages  = get_dependencies_from_file(python_files)

    # Write to file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relative_python_files = [os.path.relpath(file, folder_path) for file in python_files]
    python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()

    if os.path.exists(os.path.dirname(file_name)):
        output_file = file_name
    else: 
        output_file = os.path.join(folder_path,"dependencies.txt")
    
    with open(output_file, "w") as f:
        f.write("Software version:\n")
        f.write(f"{python_version}\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("Files checked:\n")
        f.write("\n".join(relative_python_files) + "\n\n")
        f.write("Dependencies:\n")
        for package, version in installed_packages .items():
            f.write(f"{package}=={version}\n")

    print(f"{file_name} successfully generated at {output_file}")

@ensure_correct_kernel
def main():
    get_setup_dependencies()

if __name__ == "__main__":
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    main()
{% endraw %}
"""
    write_script(folder_path, "get_dependencies", extension, content)

def create_get_r_dependencies(folder_path):
    extension = ".R"
    content = r"""
{% raw %}    
get_dependencies <- function(folder_path = NULL, file_name = "dependencies.txt",install_cmd=NULL) {
  
  # If folder_path is not provided, use the folder of the current script
  if (is.null(folder_path)) {
    folder_path <- dirname(rstudioapi::getSourceEditorContext()$path)
  }
  
  print(folder_path)
  
  # Ensure renv is installed
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  
  # Check if the folder exists
  if (!dir.exists(folder_path)) {
    stop("The specified folder does not exist.")
  }
  
  # List all .R files in the folder and subfolders (use relative paths)
  r_files <- list.files(folder_path, pattern = "\\.R$", full.names = TRUE, recursive = TRUE)
  
  if (length(r_files) == 0) {
    stop("No .R files found in the specified folder or its subfolders.")
  }
  
  # Detect dependencies using renv
  message("Analyzing dependencies in R scripts...")
  dependencies <- renv::dependencies(path = folder_path)
  
  # Extract relevant columns (package and version)
  dependency_list <- unique(dependencies[, c("Package", "Version")])
  
  # Check if the version is available, if not, use packageVersion() to get it
  dependency_list$Version[is.na(dependency_list$Version) | dependency_list$Version == ""] <- sapply(
    dependency_list$Package[is.na(dependency_list$Version) | dependency_list$Version == ""],
    function(pkg) {
      if (requireNamespace(pkg, quietly = TRUE)) {
        version <- tryCatch({
          pkg_version <- packageVersion(pkg)
          if (is.null(pkg_version)) {
            return("Not available")
          } else {
            return(as.character(pkg_version))
          }
        }, error = function(e) {
          return("Not available")
        })
        return(version)
      } else {
        return("Not available")
      }
    }
  )
  
  # Remove dependencies with "Not available" that are not used in any .R file
  not_available_dependencies <- dependency_list$Package[dependency_list$Version == "Not available"]
  
  for (pkg in not_available_dependencies) {
    # Check if the package is referenced in the 'Files checked' list, and if an .R file exists for it
    pkg_script <- file.path(folder_path, paste0(pkg, ".R"))
    
    if (!file.exists(pkg_script) || !pkg %in% basename(r_files)) {
      # If the corresponding script does not exist or is not listed, remove it from the dependency list
      message("Removing dependency '", pkg, "' as it is not used in any R script and no corresponding .R file was found.")
      dependency_list <- dependency_list[dependency_list$Package != pkg, ]
    }
  }
  
  # Create a dependencies.txtt file
  output_file <- file.path(folder_path, file_name )
  message("Writing dependencies to 'dependencies.txt'...")
  
  # Collect the R version
  r_version <- paste(R.version$version.string)
  
  # Collect the list of files checked (relative paths)
  relative_r_files <- file.path(".", gsub(paste0(normalizePath(folder_path, winslash = "/"), "/?"), "", normalizePath(r_files, winslash = "/")))
  checked_files <- paste(relative_r_files, collapse = "\n")

  # Get the current timestamp
  timestamp <- Sys.time()
  formatted_timestamp <- format(timestamp, "%Y-%m-%d %H:%M:%S")
  
# Write to the dependencies.txt file
writeLines(
  c(
    "Software version:",
    r_version,
    "",
    paste("Timestamp:", timestamp),
    "",
    "Files checked:",
    checked_files,
    "",
    if (!is.null(install_cmd)) c("Install Command:", install_cmd, ""),
    "Dependencies:"
  ),
  con = output_file
) 
  # Append dependencies to the file (excluding "Not available" packages)
  write(
    paste0(dependency_list$Package, ifelse(!is.na(dependency_list$Version) & dependency_list$Version != "", paste0("==", dependency_list$Version), "")),
    file = output_file,
    append = TRUE
  )
  
  message("'dependencies.txt' successfully generated.")
}

if (interactive()) {
  get_dependencies(NULL)
}

{% endraw %}
"""
    
    write_script(folder_path, "get_dependencies", extension, content)

def create_get_matlab_dependencies(folder_path):
    extension = ".m"
    content = r"""
{% raw %}      
function get_dependencies(folder_path,file_name,install_cmd)
    % If folder_path is not provided, use the folder of the current script
    if nargin < 1
        folder_path = fileparts(mfilename('fullpath'));
    end

    % Default dependency file
    if nargin < 2
        file_name = 'dependencies.txt';
    end

    if nargin < 3
        install_cmd = "";
    end

    % Ensure the specified folder exists
    if ~isfolder(folder_path)
        error("The specified folder does not exist.");
    end

    % Find all .m files in the folder and its subfolders
    m_files = dir(fullfile(folder_path, '**', '*.m'));
    if isempty(m_files)
        error("No .m files found in the specified folder.");
    end

    % Initialize containers for unique dependencies
    unique_files = {};
    unique_products = containers.Map;

    % Analyze each .m file
    file_paths = strings(length(m_files), 1);
    for i = 1:length(m_files)
        file_path = fullfile(m_files(i).folder, m_files(i).name);
        file_paths(i) = file_path;

        % Get required files and products
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

    % Create the output file
    output_file = fullfile(folder_path, file_name);
    fid = fopen(output_file, 'w');
    if fid == -1
        error("Unable to create dependencies.txt in the specified folder.");
    end

    % Write header information
    fprintf(fid, "Software version:"\n");
    fprintf(fid, "MATLAB version: %s\n\n", version);
    fprintf(fid, "Timestamp: %s\n\n", datestr(now, 'yyyy-mm-dd HH:MM:SS'));

    % Write files checked
    fprintf(fid, "Files checked:\n");
    for i = 1:length(file_paths)
        fprintf(fid, "%s\n", file_paths(i));
    end
    fprintf(fid, "\n");

    % Write Install Command if available
    if ~isempty(install_cmd)
        fprintf(fid, "Install Command:\n");
        fprintf(fid, "%s\n\n", install_cmd);
    end

    % Write dependencies
    fprintf(fid, "Dependencies:\n");
    % Add toolboxes
    product_names = keys(unique_products);
    for i = 1:length(product_names)
        fprintf(fid, "%s==%s\n", product_names{i}, unique_products(product_names{i}));
    end

    % Add required files
    for i = 1:length(unique_files)
        [~, name, ext] = fileparts(unique_files{i});
        fprintf(fid, "%s%s==Not available\n", name, ext);
    end

    fclose(fid);
    fprintf("dependencies.txt successfully generated in %s.\n", folder_path);
end
{% endraw %}
"""
    write_script(folder_path, "get_dependencies", extension, content)

# FIX ME 
def create_get_sas_dependencies(folder_path):
    extension = ".m"
    content = r"""
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

    %put dependencies.txt successfully generated at &folder_path.\\dependencies.txt;
%mend get_dependencies;

/* Example usage */
%get_dependencies(C:\\path\\to\\your\\folder);
{% endraw %}
"""
    write_script(folder_path, "get_sas_dependencies", extension, content)

# FIX ME 
def create_get_stata_dependencies(folder_path):

    extension = ".do"
    content = r"""
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


# Create install_dependencies()  # FIX ME - NOT IN USE!!!
def create_install_dependencies(programming_language, folder_path):
    """
    Create the install_dependencies script for the specified programming_language.
    
    Parameters:
    programming_language (str): The programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the install_dependencies script will be saved.
    """

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
    content = r"""
{% raw %}    
import subprocess
import sys
import re
import importlib.util

def parse_dependencies(file_path='dependencies.txt'):
    required_libraries = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Flag to start reading dependencies section
        reading_dependencies = False
        
        for line in lines:
            # Check for the start of the dependencies section
            if 'Dependencies:' in line:
                reading_dependencies = True
                continue  # Skip the "Dependencies:" line
            
            # If we are in the dependencies section, extract the library names
            if reading_dependencies:
                # Stop reading if we encounter an empty line or another section
                if line.strip() == '':
                    break
                
                # Regex to match package names and versions
                match = re.match(r'(\S+)(==\S+)?', line.strip())
                if match:
                    lib_name = match.group(1)
                    version = match.group(2) if match.group(2) else None
                    
                    # Ignore libraries with 'Not available' as they don't need to be installed
                    if version != 'Not available':
                        required_libraries.append(f"{lib_name}{version if version else ''}")
                
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []

    return required_libraries

def is_standard_library(lib_name):
    spec = importlib.util.find_spec(lib_name)
    return spec is not None and spec.origin is None  # Origin None means it's built-in

def install_dependencies(required_libraries):
    # Get list of installed libraries
    installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

    # Check and install missing libraries
    for lib in required_libraries:
        try:
            # Extract library name (without version) for checking
            lib_name = lib.split('==')[0]
            
            # Skip installation for standard libraries
            if is_standard_library(lib_name):
                print(f"Skipping installation of standard library: {lib_name}")
                continue

            # Check if the library is already installed
            if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
            else:
                print(f"{lib} is already installed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {lib}: {e}")

@ensure_correct_kernel
def main(dependencies_file='dependencies.txt'):
    # Parse the dependencies from the text file
    required_libraries = parse_dependencies(dependencies_file)
    
    # Install the missing dependencies
    if required_libraries:
        install_dependencies(required_libraries)
    else:
        print("No dependencies found to install.")

if __name__ == "__main__":
    main('dependencies.txt')  # Specify the dependencies file here
{% endraw %}
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_r_dependencies(folder_path):
    """
    Create the install_dependencies script for R to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".R"
    content = r"""
{% raw %}    
install_dependencies <- function(file_path = NULL) {
  # If no file_path is specified, look for dependencies.txt in the script folder
  if (is.null(file_path)) {
    file_path <- file.path(dirname(rstudioapi::getActiveDocumentContext()$path), "dependencies.txt")
  }
  
  # Define a function to read dependencies from a text file and return them as a list
  get_txt_dependencies <- function(file_path) {
    # Check if the file exists
    if (!file.exists(file_path)) {
      stop("Dependency file not found at: ", file_path)
    }
    
    # Read the file
    lines <- readLines(file_path)
    
    # Find the lines that contain package dependencies (they will have '==')
    dependency_lines <- grep("==", lines, value = TRUE)
    
    # Split the lines into package names and versions
    dependencies <- sapply(dependency_lines, function(line) {
      parts <- strsplit(line, "==")[[1]]
      package_name <- trimws(parts[1])
      package_version <- trimws(parts[2])
      list(name = package_name, version = package_version)
    }, simplify = FALSE)
    
    return(dependencies)
  }

  # Get the dependencies from the file
  dependencies <- get_txt_dependencies(file_path)
  
  # Extract package names and versions into vectors
  required_packages <- sapply(dependencies, function(dep) dep$name)
  package_versions <- sapply(dependencies, function(dep) dep$version)

  # Install packages if they are not already installed or if the installed version is different
  for (i in 1:length(required_packages)) {
    pkg <- required_packages[i]
    version <- package_versions[i]
    
    # Check if package is installed
    if (!require(pkg, character.only = TRUE)) {
      install.packages(pkg)
    }
    
    # Check if the installed version is correct, and reinstall if needed
    current_version <- packageVersion(pkg)
    if (as.character(current_version) != version) {
      install.packages(pkg)
    }
  }
}
{% endraw %}
"""
    write_script(folder_path, "install_dependencies", extension, content)

def create_install_matlab_dependencies(folder_path):
    """
    Create the install_dependencies script for Matlab to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".m"
    content = r"""
{% raw %}  
function install_dependencies(dependency_file)
    % Default dependency file
    if nargin < 1
        dependency_file = 'dependencies.txt';
    end

    % Check if the dependency file exists
    if ~isfile(dependency_file)
        error("Dependency file '%s' does not exist.", dependency_file);
    end

    % Read the dependency file
    fid = fopen(dependency_file, 'r');
    if fid == -1
        error("Unable to open the dependency file '%s'.", dependency_file);
    end
    dependency_lines = textscan(fid, '%s', 'Delimiter', '\n');
    fclose(fid);
    dependency_lines = dependency_lines{1};

    % Extract MATLAB version from the file
    matlab_version_line = dependency_lines{startsWith(dependency_lines, 'MATLAB version:')};
    expected_version = strtrim(strrep(matlab_version_line, 'MATLAB version:', ''));

    % Check MATLAB version
    current_version = version;
    if ~strcmp(current_version, expected_version)
        error("MATLAB version mismatch! Current version: %s, Expected version: %s.", current_version, expected_version);
    end
    fprintf("MATLAB version check passed: %s\n", current_version);

    % Extract dependencies
    dependencies_start = find(startsWith(dependency_lines, 'Dependencies:')) + 1;
    dependencies = dependency_lines(dependencies_start:end);

    % Attempt to install missing toolboxes
    for i = 1:length(dependencies)
        line = strtrim(dependencies{i});
        if isempty(line)
            continue;
        end

        % Parse toolbox or file
        tokens = regexp(line, '^(.*?)==(.+)$', 'tokens');
        if isempty(tokens)
            continue;
        end
        dependency_name = strtrim(tokens{1}{1});
        dependency_version = strtrim(tokens{1}{2});

        % Skip if the dependency is a file
        if strcmp(dependency_version, 'Not available')
            fprintf("Skipping file dependency: %s\n", dependency_name);
            continue;
        end

        % Check if the toolbox is installed
        installed_toolboxes = matlab.addons.installedAddons();
        if any(strcmp(installed_toolboxes.Name, dependency_name))
            fprintf("Toolbox '%s' is already installed.\n", dependency_name);
        else
            % Attempt to install the toolbox
            fprintf("Installing toolbox: %s (Version: %s)...\n", dependency_name, dependency_version);
            try
                matlab.addons.installToolbox(dependency_name);
                fprintf("Successfully installed toolbox: %s\n", dependency_name);
            catch e
                fprintf("Failed to install toolbox '%s': %s\n", dependency_name, e.message);
            end
        end
    end

    fprintf("Dependency installation process completed.\n");
end
{% endraw %}
"""
    write_script(folder_path, "install_dependencies", extension, content)

# FIX ME 
def create_install_stata_dependencies(folder_path):
    """
    Create the install_dependencies script for Stata to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".do"
    content = r"""
* Install Stata dependencies

* List of required packages
ssc install outreg2, replace
ssc install estout, replace
net install rdrobust, from("https://www.example.com/rdrobust"), replace
"""
    write_script(folder_path, "install_dependencies", extension, content)

# FIX ME 
def create_install_sas_dependencies(folder_path):
    """
    Create the install_dependencies script for SAS to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".sas"
    content = r"""
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
    if programming_language.lower() not in ["python","r","matlab","stata","sas"]:
        return
    
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
    extension = ".ipynb"
    script_name = "workflow"

    content = nbf.v4.new_notebook()

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
    content.cells.extend(cells)

    write_script(folder_path, script_name, extension, content)

def create_r_notebook(folder_path):
    extension = ".Rmd"
    script_name = "workflow"
    # Create RMarkdown content with the requested structure
    content = dedent(r"""{% raw %}
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

    write_script(folder_path, script_name, extension, content)

def create_stata_notebook(folder_path):
    extension = ".ipynb"
    script_name = "workflow"

    content = nbf.v4.new_notebook()

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
    content.cells.extend(cells)

    write_script(folder_path, script_name, extension, content)

def create_matlab_notebooks(folder_path):
  
    # Create Jupyter notebook using jupyter-matlab-proxy
    extension = ".ipynb"
    script_name = "workflow"

    content= nbf.v4.new_notebook()

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

    content.cells.extend(cells)

    write_script(folder_path, script_name, extension, content)
   
    # Create MATLAB notebook (.mlx) and Jupyter notebook
    extension = ".mlx"
    script_name = "workflow"

    # For .mlx file, write MATLAB-specific workflow
    content = dedent(r"""%% Workflow: Running all steps in order
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

    write_script(folder_path, script_name, extension, content)

def create_sas_notebook(folder_path):
  

    extension = ".ipynb"
    script_name = "workflow"
    
    content= nbf.v4.new_notebook()

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
    content.cells.extend(cells)
    
    write_script(folder_path, script_name, extension, content)


@ensure_correct_kernel
def main():

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
  
    # Create scripts and notebook
    create_scripts(programming_language, "./src")
    create_notebooks(programming_language, "./notebooks")

    
if __name__ == "__main__":

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()