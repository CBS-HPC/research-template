import os
from textwrap import dedent
import pathlib

from .general_tools import *
from .jinja_tools import *


def create_scripts(programming_language):
    """
    Creates a project structure with specific scripts for data science tasks
    and a workflow script in R or Python.
    
    Parameters:
    programming_language (str): "r" for R, "python" for Python.
    folder_path (str): The directory where the scripts will be saved.
    """
    programming_language = programming_language.lower()
    ext = ext_map.get(programming_language)

    if ext is None:
        return f"Unsupported programming language: {programming_language}"
   
    folder_path = language_dirs.get(programming_language)

    # Script details based on purpose
    scripts = {"s00_main": "",
        "s01_install_dependencies": "Helper to intall dependencies",
        "s02_utils": "Helper functions or utilities",
        "s03_data_collection": "Data extraction/scraping",
        "s04_preprocessing": "Data cleaning, transformation, feature engineering",
        "s05_modeling": "Training and evaluation of models",
        "s06_visualization": "Functions for plots and visualizations",
        "get_dependencies": ""
    }


    # Create the individual step scripts
    for script_name, purpose in scripts.items():
        create_step_script(programming_language, folder_path, script_name, purpose)

    # Create the workflow script that runs all steps
    create_main(programming_language, folder_path,file_name = "s00_main")

    # Create Notebooks
    create_notebooks(programming_language, folder_path,file_name = "s00_workflow")

    # Create get_dependencies
    create_get_dependencies(programming_language, folder_path,file_name = "get_dependencies")

    # Create Install_dependencies
    create_install_dependencies(programming_language, folder_path,file_name = "s01_install_dependencies")

    # Create unit-test test files
    generate_root_level_tests(programming_language, scripts)

# Orchstration scripts 
def create_step_script(programming_language, folder_path, script_name, purpose):
    """
    Main function to create a step script (R, Python, Stata, Matlab, or SAS) with the necessary structure.
    
    Parameters:
    programming_language (str): Programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the script will be saved.
    script_name (str): The name of the script (e.g., 's03_data_collection', 's04_preprocessing').
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

def create_main(programming_language, folder_path,file_name = "s00_main"):
    """
    Main function to create a workflow script that runs all steps in order for the specified programming_language.
    
    Parameters:
    programming_language (str): Programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the workflow script will be saved.
    """
 
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_r_main(folder_path,file_name)
    elif programming_language.lower() == "python":
        create_python_main(folder_path,file_name)
    elif programming_language.lower() == "stata":
        create_stata_main(folder_path,file_name)
    elif programming_language.lower() == "matlab":
        create_matlab_main(folder_path,file_name)
    elif programming_language.lower() == "sas":
        create_sas_main(folder_path,file_name)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_install_dependencies(programming_language, folder_path,file_name = "s01_install_dependencies"):
    """
    Create the install_dependencies script for the specified programming_language.
    
    Parameters:
    programming_language (str): The programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the install_dependencies script will be saved.
    """

    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_install_r_dependencies(folder_path,file_name)
    elif programming_language.lower() == "python":
        create_install_python_dependencies(folder_path,file_name)
    elif programming_language.lower() == "stata":
        create_install_stata_dependencies(folder_path,file_name)
    elif programming_language.lower() == "matlab":
        create_install_matlab_dependencies(folder_path,file_name)
    elif programming_language.lower() == "sas":
        create_install_sas_dependencies(folder_path,file_name)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_get_dependencies(programming_language, folder_path,file_name = "get_dependencies"):
    """
    Create the install_dependencies script for the specified programming_language.
    
    Parameters:
    programming_language (str): The programming language (e.g., "r", "python", "stata", "matlab", "sas").
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
  
    # Call the appropriate function based on the language
    if programming_language.lower() == "r":
        create_get_r_dependencies(folder_path,file_name)
    elif programming_language.lower() == "python":
        create_get_python_dependencies(folder_path,file_name)
    elif programming_language.lower() == "stata":
        create_get_stata_dependencies(folder_path,file_name)
    elif programming_language.lower() == "matlab":
        create_get_matlab_dependencies(folder_path,file_name)
    elif programming_language.lower() == "sas":
        create_get_sas_dependencies(folder_path,file_name)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def create_notebooks(programming_language, folder_path,file_name = "s00_workflow"):
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
        create_python_notebook(folder_path,file_name)
    elif programming_language.lower() == "r":
        create_r_notebook(folder_path,file_name)
    elif programming_language.lower() == "stata":
        create_stata_notebook(folder_path,file_name)
    elif programming_language.lower() == "matlab":
        create_matlab_notebook(folder_path,file_name)
    elif programming_language.lower() == "sas":
        create_sas_notebook(folder_path,file_name)
    else:
        raise ValueError("Invalid programming_language choice. Please specify 'r', 'python', 'stata', 'matlab', or 'sas'.")

def generate_root_level_tests(programming_language, scripts):
    """
    Creates unit test stubs in a top-level tests/ folder for a given programming language.

    Parameters:
        language (str): One of 'python', 'r', 'matlab', 'stata'
        base_dir (str): Base directory of the project (default is current dir)
    """
    programming_language = programming_language.lower()

    if programming_language == "r":
        folder_path = "./tests/testthat"
        extension = ".R"
    elif programming_language == "stata":
        folder_path = "./tests"
        extension = ".do"
    elif programming_language == "matlab":
        folder_path = "./tests"
        extension = ".m"
    elif programming_language == "python":
        folder_path = "./tests"
        extension = ".py"
    else:
        raise ValueError(f"Unsupported language: {programming_language}")


    for base, _ in scripts.items():
        script_name = f"test_{base}"
    
        if programming_language == "python":
            content = f'def test_{base}():\n    assert True  # Add real tests for {base}.py\n'
        elif programming_language == "r":
            content = f"""{% raw %}test_that("{base} runs", {{\n  expect_true(TRUE)\n}})\n{% endraw %}"""

        elif programming_language == "matlab":
            content = f"""{% raw %}function tests = test_{base}\n
                tests = functiontests(localfunctions);\n
                end\n\n
                function test_case(testCase)\n
                verifyTrue(testCase, true)\n
                end\n
                {% endraw %}"""
        elif programming_language == "stata":
            content = f"""{% raw %}
                clear all\n
                set more off\n
                display "Testing {base}"\n
                assert 1 == 1\n
                {% endraw %}"""
            

        write_script(folder_path, script_name, extension, content)

    print(f"✅ Created test files for {programming_language} in {folder_path}")


# Python
def create_python_script(folder_path, script_name, purpose):
    extension = ".py"
    content = f"""
# {purpose} code

import os
import sys
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_data = os.path.join(base_path, "data", "00_raw")
interim_data = os.path.join(base_path, "data", "01_interim")
processed_data = os.path.join(base_path, "data", "02_processed")
setup_path = os.path.join(base_path, "setup") 
sys.path.append(setup_path)
from s02_utils import *

@ensure_correct_kernel
def main():
    # {purpose} code
    print("Running {script_name}...")

if __name__ == "__main__":
    main()
"""
    write_script(folder_path, script_name, extension, content)

def create_python_main(folder_path,file_name):
    extension = ".py"
    content = f"""{% raw %}
# Main: Running all steps in order

import os
import sys

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
code_path = os.path.join(base_path, "src")
sys.path.append(code_path)

@ensure_correct_kernel
def main():
    # Install dependencies
    import s01_install_dependencies
    s01_install_dependencies.main()

    # Load utility functions (not executed directly)
    import s02_utils  # <- provides helper functions

    # Load main workflow scripts
    import s03_data_collection
    import s04_preprocessing
    import s05_modeling
    import s06_visualization

    # Run data collection
    s03_data_collection.main()

    # Run preprocessing
    s04_preprocessing.main()

    # Run modeling
    s05_modeling.main()

    # Run visualization
    s06_visualization.main()

if __name__ == "__main__":
    main()
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_get_python_dependencies(folder_path,file_name):
    extension = ".py"
    content = r"""{% raw %}import os
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

def resolve_parent_module(module_name):
    if '.' in module_name:
        return module_name.split('.')[0]
    return module_name

def get_setup_dependencies(folder_path: str = None, file_name: str = "dependencies.txt"):
    
    def extract_code_from_notebook(path):
        code_cells = []
        try:
            nb = nbformat.read(path, as_version=4)
            for cell in nb.cells:
                if cell.cell_type == "code":
                    code_cells.append(cell.source)
        except Exception as e:
            print(f"Could not parse notebook {path}: {e}")
        return "\n".join(code_cells)

    def get_dependencies_from_file(python_files):
        used_packages = set()

        for file in python_files:
            try:
                if file.endswith(".ipynb"):
                    code = extract_code_from_notebook(file)
                else:
                    with open(file, "r", encoding="utf-8") as f:
                        code = f.read()

                tree = ast.parse(code, filename=file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            used_packages.add(resolve_parent_module(alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        used_packages.add(resolve_parent_module(node.module))

            except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
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

    if folder_path is None:
        folder_path = os.path.dirname(os.path.abspath(__file__))

    print(f"Scanning folder: {folder_path}")
    python_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py") or file.endswith(".ipynb"):
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
    write_script(folder_path, file_name, extension, content)

def create_install_python_dependencies(folder_path,file_name):
    """
    Creates a script to install required Python dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies.py script will be saved.
    """
    extension = ".py"
    content = r"""{% raw %}    
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
    write_script(folder_path, file_name, extension, content)

def create_python_notebook(folder_path,file_name = "s00_workflow"):
    extension = ".ipynb"
   
    content = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running All Steps in Order"),

        nbf.v4.new_markdown_cell("### Install dependencies"),
        nbf.v4.new_code_cell(
            "import sys\n"
            "import os\n"
            "base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))\n"
            "code_path = os.path.join(base_path, 'src')\n"
            "if code_path not in sys.path:\n"
            "    sys.path.append(code_path)\n"
            "import s01_install_dependencies\n"
            "s01_install_dependencies.main()"
        ),

        nbf.v4.new_markdown_cell("### Load Scripts"),
        nbf.v4.new_code_cell(
            "import s02_utils  # helper functions only, not executed directly\n"
            "import s03_data_collection\n"
            "import s04_preprocessing\n"
            "import s05_modeling\n"
            "import s06_visualization"
        ),

        nbf.v4.new_markdown_cell("### Run Data Collection"),
        nbf.v4.new_code_cell("s03_data_collection.main()"),

        nbf.v4.new_markdown_cell("### Run Preprocessing"),
        nbf.v4.new_code_cell("s04_preprocessing.main()"),

        nbf.v4.new_markdown_cell("### Run Modeling"),
        nbf.v4.new_code_cell("s05_modeling.main()"),

        nbf.v4.new_markdown_cell("### Run Visualization"),
        nbf.v4.new_code_cell("s06_visualization.main()")
    ]

    content.cells.extend(cells)

    write_script(folder_path, file_name, extension, content)

# R
def create_r_script(folder_path, script_name, purpose):
    extension = ".R"
    content = f"""{% raw %}
# {purpose} code

base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
raw_data <- file.path(base_path, "data", "00_raw")
interim_data <- file.path(base_path, "data", "01_interim")
processed_data <- file.path(base_path, "data", "02_processed")

main <- function() {{
    # {purpose} code
    print('Running {script_name}...')
}}


main()

{% endraw %}
"""
    
    write_script(folder_path, script_name, extension, content)

def create_r_main(folder_path,file_name):
    extension = ".R"
    content = f"""{% raw %}
# Main: Running all steps in order

# Install dependencies
source('s01_install_dependencies.R')

# Load utilities
source("s02_utils.R")  # <- shared functions, not a step

# Load Scripts
source('s03_data_collection.R')
source('s04_preprocessing.R')
source('s05_modeling.R')
source('s06_visualization.R')

## Run data collection
s03_data_collection$main()

## Run preprocessing
s04_preprocessing$main()

## Run modeling
s05_modeling$main()

## Run visualization
s06_visualization$main()
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_get_r_dependencies(folder_path,file_name):
    extension = ".R"
    content = r"""{% raw %}install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE))
    install.packages("renv")
  library(renv)
  if (!requireNamespace("jsonlite", quietly = TRUE))
    install.packages("jsonlite")
  library("jsonlite")
  message("renv installed and loaded.")
}

get_project_root <- function(path = NULL) {
  # --- Helper: Add 'R' if it exists ---
  append_code_if_exists <- function(root) {
    code_path <- file.path(root, "R")
    if (dir.exists(code_path)) {
      return(code_path)
    }
    return(root)
  }
  
  # 1) Explicit path supplied by the caller
  if (!is.null(path)) {
    #path <- normalizePath(path, winslash = "/")
    path <- normalizePath(path, winslash = .Platform$file.sep)
    root <- if (file.exists(path) && !dir.exists(path)) dirname(path) else path
    root <- append_code_if_exists(root)
    return(root)
  }
  
  # 2) RStudio active document
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    doc <- rstudioapi::getActiveDocumentContext()$path
    if (nzchar(doc)) {
      root <- dirname(normalizePath(doc, winslash = "/"))
      if (grepl("/R$", root)) {
        return(root)  # Already in "R"
      }
      root <- append_code_if_exists(root)
      message("Detected project root (RStudio): ", root)
      return(root)
    }
  }
  
  # 3) Command-line runs (R, Rscript, etc.)
  args <- commandArgs(trailingOnly = FALSE)
  
  # Match both --file=script.R and -f script.R
  file_arg <- NULL
  
  # Handle --file=script.R
  long_file <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  
  # Handle -f script.R
  short_idx <- which(args == "-f")
  if (length(short_idx) > 0 && short_idx < length(args)) {
    short_file <- args[short_idx + 1]
  } else {
    short_file <- character(0)
  }
  
  file_arg <- c(long_file, short_file)
  file_arg <- file_arg[nzchar(file_arg)][1]  # Use the first non-empty match
  
  # 4) Fallback - working directory
  if (length(file_arg)) {
    root <- dirname(normalizePath(file_arg, winslash = "/"))
  } else {
    root <- normalizePath(getwd(), winslash = "/")
  }
  
  # Handle /R edge case
  if (!grepl("/R$", root)) {
    root <- append_code_if_exists(root)
  }
  
  message("Detected project root: ", root)
  return(root)
}

ensure_project_loaded <- function(folder_path) {
  if (!identical(renv::project(), normalizePath(folder_path))) {
    renv::load(folder_path, quiet = TRUE)
    message("renv project loaded.")
  }
}

renv_init <- function(folder_path) {
  lockfile <- file.path(folder_path, "renv.lock")
  if (!file.exists(lockfile)) {
    renv::init(project = folder_path, bare = TRUE, force = TRUE)
    message("renv infrastructure created.")
  } else {
    message("renv infrastructure already exists.")
  }
  
  renv::install(c("jsonlite", "rmarkdown", "rstudioapi","testthat"))

  # Load to make sure they are added to .lock file
  library(testthat)
  library(jsonlite)
  library(rmarkdown)
  library(rstudioapi)
  
}

safely_snapshot <- function(folder_path) {
  tryCatch({
    renv::snapshot(project = folder_path, prompt = FALSE)
    message("renv.lock written / updated.")
  }, error = function(e) {
    message("Snapshot failed: ", e$message)
  })
}

auto_snapshot <- function(folder_path, do_restore = FALSE) {
  ensure_project_loaded(folder_path)
  
  lockfile_path <- file.path(folder_path, "renv.lock")
  
  if (file.exists(lockfile_path)) {
    # Step 1: Find all declared dependencies
    message("Checking for missing packages ...")
  
    deps <- renv::dependencies(path = folder_path)
    used_packages <- unique(deps$Package)
    #installed <- rownames(installed.packages(lib.loc = renv::paths$library(project = folder_path)))
    installed <- rownames(installed.packages())
    missing <- setdiff(used_packages, installed)
    
    # Step 2: Preemptively install missing packages (suppress prompts)
    if (length(missing) > 0) {
      message("Installing missing packages: ", paste(missing, collapse = ", "))
      renv::install(missing)
      #install.packages(missing, quiet = TRUE)
    } else {
      message("All required packages are already installed.")
    }
    
    if (do_restore) {
      message("Restoring packages from lockfile ...")
      #renv::restore(project = folder_path, prompt = FALSE)
      renv_restore(folder_path = folder_path,check_r_version = TRUE )
    }
    
  } else {
    message("No renv.lock found. Skipping restore.")
  }
  
  # Step 4: Snapshot without prompt
  message("Creating snapshot ...")
  safely_snapshot(folder_path)
}

renv_restore <- function(folder_path, check_r_version = TRUE) {
  ensure_project_loaded(folder_path)
  
  lockfile_path <- file.path(folder_path, "renv.lock")
  
  if (!file.exists(lockfile_path)) {
    stop("Cannot restore: renv.lock file not found at ", lockfile_path)
  }
  
  if (check_r_version) {
    lock <- tryCatch(
      jsonlite::read_json(lockfile_path),
      error = function(e) {
        stop("Failed to parse renv.lock: ", e$message)
      }
    )
    
    expect <- lock$R$Version
    have   <- paste(R.version$major, R.version$minor, sep = ".")
    
    if (!identical(expect, have)) {
      warning(sprintf(
        "R version mismatch:\n  - Current:  %s\n  - Expected: %s (from lockfile)", 
        have, expect
      ))
      # If you want to abort instead, replace `warning(...)` with `stop(...)`
    }
  }
  
  renv::restore(project = folder_path, prompt = FALSE)
  message("Packages restored from lockfile.")
}

generate_dependencies_file <- function(folder_path, file_name = "dependencies.txt") {
  # List all .R files in the folder and subfolders (use relative paths)
  all_files <- list.files(folder_path, pattern = "\\.R$", full.names = TRUE, recursive = TRUE)
  
  r_files <- all_files[!grepl("/renv/", all_files)]
  
  if (length(r_files) == 0) {
    stop("No .R files found in the specified folder or its subfolders.")
  }
  
  # Detect dependencies using renv
  message("Analyzing dependencies in R scripts...")
  dependencies <- renv::dependencies(path = folder_path)
  
  # Extract relevant columns (Package and Version)
  dependency_list <- unique(dependencies[, c("Package", "Version")])
  
  # Fill in missing versions using packageVersion()
  missing_version_idx <- is.na(dependency_list$Version) | dependency_list$Version == ""
  dependency_list$Version[missing_version_idx] <- sapply(
    dependency_list$Package[missing_version_idx],
    function(pkg) {
      if (requireNamespace(pkg, quietly = TRUE)) {
        tryCatch(as.character(packageVersion(pkg)), error = function(e) "Not available")
      } else {
        "Not available"
      }
    }
  )
  
  # Remove unused "Not available" dependencies
  not_available <- dependency_list$Package[dependency_list$Version == "Not available"]
  for (pkg in not_available) {
    pkg_script <- file.path(folder_path, paste0(pkg, ".R"))
    if (!file.exists(pkg_script) || !any(grepl(pkg, basename(r_files)))) {
      message("Removing unused or unreferenced dependency: '", pkg, "'")
      dependency_list <- dependency_list[dependency_list$Package != pkg, ]
    }
  }
  
  # Prepare output path
  output_file <- file.path(folder_path, file_name)
  
  # Metadata
  r_version <- paste(R.version$version.string)
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  relative_r_files <- file.path(".", gsub(paste0(normalizePath(folder_path, winslash = "/"), "/?"), "", normalizePath(r_files, winslash = "/")))
  checked_files <- paste(relative_r_files, collapse = "\n")
  
  # Write header and metadata
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
      "Dependencies:"
    ),
    con = output_file
  )
  
  # Append dependency list
  dep_lines <- paste0(dependency_list$Package, ifelse(!is.na(dependency_list$Version) & dependency_list$Version != "", paste0("==", dependency_list$Version), ""))
  write(dep_lines, file = output_file, append = TRUE)
  
  message("'", file_name, "' successfully generated at ", output_file)
}

get_dependencies <- function(folder_path, file_name = "dependencies.txt"){
  install_renv()
  renv_init(folder_path)      # create renv/ if missing
  #renv_snapshot(folder_path)  # write renv.lock (non-interactive)
  auto_snapshot(folder_path, do_restore = FALSE)
  generate_dependencies_file(folder_path,file_name )
  #renv_restore(folder_path, check_r_version = TRUE)  
  
}

# ------------------------------ main -----------------------------------------

args       <- commandArgs(trailingOnly = TRUE)
folder_path  <- if (length(args)) args[1] else get_project_root()

get_dependencies(folder_path, file_name = "dependencies.txt")

{% endraw %}
"""
    
    write_script(folder_path, file_name, extension, content)

def create_install_r_dependencies(folder_path,file_name):
    """
    Create the install_dependencies script for R to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".R"
    content = r"""{% raw %}    
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
    write_script(folder_path, file_name, extension, content)

def create_r_notebook(folder_path,file_name = "s00_workflow"):
    extension = ".Rmd"
    # Create RMarkdown content with the requested structure
    content = dedent(r"""{% raw %}
    ---
    title: "Workflow: Running All Steps in Order"
    output: html_document
    ---

    # Workflow

    ## Install Dependencies
    ```{r}
    source("s01_install_dependencies.R")
    ```

    ## Load Utility and Workflow Scripts
    ```{r}
    source("s02_utils.R")  # shared helper functions, not executed directly
    source("s03_data_collection.R")
    source("s04_preprocessing.R")
    source("s05_modeling.R")
    source("s06_visualization.R")
    ```

    ## Run Data Collection
    ```{r}
    data_collection$main()
    ```

    ## Run Preprocessing
    ```{r}
    preprocessing$main()
    ```

    ## Run Modeling
    ```{r}
    modeling$main()
    ```

    ## Run Visualization
    ```{r}
    visualization$main()
    ```
    {% endraw %}""")

    write_script(folder_path, file_name, extension, content)

# Matlab
def create_matlab_script(folder_path, script_name, purpose):
    extension = ".m"
    content = f"""
% {purpose} code

base_path = fullfile(fileparts(mfilename('fullpath')), '..');
raw_data = fullfile(base_path, 'data', '00_raw');
interim_data = fullfile(base_path, 'data', '01_interim');
processed_data = fullfile(base_path, 'data', '02_processed');

function {script_name}_main()
    % {purpose} code
    disp('Running {script_name}...');
end

if ~isdeployed
    {script_name}_main();
end
"""
    write_script(folder_path, script_name, extension, content)

def create_matlab_main(folder_path,file_name):
    extension = ".m"
    content = f"""{% raw %}
% Main: Running all steps in order

% Install dependencies
run('s01_install_dependencies.m');

% Load utility functions (not executed)
run('s02_utils.m');

% Run data collection
s03_data_collection_main();

% Run preprocessing
s04_preprocessing_main();

% Run modeling
s05_modeling_main();

% Run visualization
s06_visualization_main();
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_get_matlab_dependencies(folder_path,file_name):
    extension = ".m"
    content = r"""{% raw %}function get_dependencies(folder_path, file_name)
    % Initializes a MATLAB project and tracks dependencies for all .m and .mlx files in the src/ folder and its subfolders.
    %
    % Usage:
    %   get_dependencies()                 - Uses current script folder
    %   get_dependencies(folder_path)      - Uses specified folder path
    %   get_dependencies(folder_path,file) - Uses specified folder and file name for dependencies.txt

    if nargin < 1
        folder_path = mfilename('fullpath');
    end

    if nargin < 2
        file_name = "dependencies.txt";
    end

    % --- Determine project directory and name ---
    folder_path = fileparts(folder_path);

    % --- File paths ---
    depFile = fullfile(folder_path, file_name);

    % --- Recursively find all .m and .mlx files in src and subfolders ---
    mFiles = dir(fullfile(folder_path, '**', '*.m'));
    mlxFiles = dir(fullfile(folder_path, '**', '*.mlx'));
    allCodeFiles = [mFiles; mlxFiles];

    % --- Analyze dependencies ---
    allFiles = {};
    allProducts = [];
    fileReports = cell(size(allCodeFiles));

    for i = 1:length(allCodeFiles)
        filePath = fullfile(allCodeFiles(i).folder, allCodeFiles(i).name);
        try
            fprintf("Analyzing dependencies for: %s\n", filePath);
            [files, products] = matlab.codetools.requiredFilesAndProducts(filePath);

            allFiles = [allFiles, files];
            allProducts = [allProducts, products];
            fileReports{i} = struct('path', filePath, 'status', 'OK', 'message', '');
        catch ME
            fprintf("Skipping due to syntax error: %s\n", filePath);
            fprintf("%s\n", ME.message);
            fileReports{i} = struct('path', filePath, 'status', 'ERROR', 'message', ME.message);
        end
    end

    % --- Unique products ---
    productNames = string({allProducts.Name});
    productVersions = string({allProducts.Version});
    [~, ia] = unique(productNames);
    uniqueProducts = containers.Map(productNames(ia), productVersions(ia));

    % --- Write to depFile ---
    fid = fopen(depFile, 'w');
    if fid == -1
        error("Unable to create %s in the specified folder.", file_name);
    end

    % Header info
    fprintf(fid, "Software version:\n");
    fprintf(fid, "MATLAB version: %s\n\n", version);
    fprintf(fid, "Timestamp: %s\n\n", datestr(now, 'yyyy-mm-dd HH:MM:SS'));

    % Files checked
    fprintf(fid, "Files checked:\n");
    for i = 1:length(fileReports)
        % Relative path with normalized separators
        relPath = erase(fileReports{i}.path, folder_path);
        relPath = strrep(relPath, filesep, '/');
        relPath = regexprep(relPath, '^/', '');

        if strcmp(fileReports{i}.status, 'OK')
            fprintf(fid, "%s\n", relPath);
        else
            fprintf(fid, "%s ERROR:\n %s\n", relPath, fileReports{i}.message);
        end
    end
    fprintf(fid, "\n");

    % Toolboxes
    fprintf(fid, "Dependencies:\n");
    productKeys = keys(uniqueProducts);
    for i = 1:length(productKeys)
        fprintf(fid, "%s==%s\n", productKeys{i}, uniqueProducts(productKeys{i}));
    end

    fclose(fid);
    fprintf("%s successfully written in %s\n", file_name, depFile);
end
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_install_matlab_dependencies(folder_path,file_name):
    """
    Create the install_dependencies script for Matlab to install required dependencies.
    
    Parameters:
    folder_path (str): The directory where the install_dependencies script will be saved.
    """
    extension = ".m"
    content = """{% raw %}  
function s01_install_dependencies(dependency_file)
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
    write_script(folder_path, file_name, extension, content)

def create_matlab_notebook(folder_path,file_name = "s00_workflow"):
    # --- 1. Create Jupyter Notebook (.ipynb) with MATLAB kernel ---
    extension = ".ipynb"
    content = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running All Steps in Order (MATLAB)"),

        nbf.v4.new_markdown_cell("### MATLAB Setup (via jupyter-matlab-proxy)"),
        nbf.v4.new_code_cell(
            "%%matlab\n"
            "% Add project source path to MATLAB\n"
            "addpath(fullfile(pwd, 'src'));\n"
            "run('s01_install_dependencies.m');"
        ),

        nbf.v4.new_markdown_cell("### Run Data Collection"),
        nbf.v4.new_code_cell("%%matlab\n"
                             "s03_data_collection_main();"),

        nbf.v4.new_markdown_cell("### Run Preprocessing"),
        nbf.v4.new_code_cell("%%matlab\n"
                             "s04_preprocessing_main();"),

        nbf.v4.new_markdown_cell("### Run Modeling"),
        nbf.v4.new_code_cell("%%matlab\n"
                             "s05_modeling_main();"),

        nbf.v4.new_markdown_cell("### Run Visualization"),
        nbf.v4.new_code_cell("%%matlab\n"
                             "s06_visualization_main();")
    ]

    content.cells.extend(cells)
    write_script(folder_path, file_name, extension, content)

    # --- 2. Create MATLAB Live Script (.mlx) version ---
    extension = ".mlx"
    content = dedent("""\
    %% Workflow: Running All Steps in Order
    % MATLAB Setup
    addpath(fullfile(pwd, 'src'));
    run('s01_install_dependencies.m');

    %% Run Data Collection
    data_collection_main();

    %% Run Preprocessing
    preprocessing_main();

    %% Run Modeling
    modeling_main();

    %% Run Visualization
    visualization_main();
    """)
    write_script(folder_path, file_name, extension, content)


# Stata

def create_stata_script(folder_path, script_name, purpose):
    extension = ".do"
    content = f"""
* {purpose} code

global base_path ".."
global raw_data "$base_path/data/00_raw"
global interim_data "$base_path/data/01_interim"
global processed_data "$base_path/data/02_processed"

program define {script_name}_main
    display "Running {script_name}..."
end

main
"""
    write_script(folder_path, script_name, extension, content)

def create_stata_main(folder_path,file_name):
    extension = ".do"
    content = f"""{% raw %}
* Main: Running all steps in order

* Install dependencies
do "s01_install_dependencies.do"

* Load utility functions (not executed directly)
do "s02_utils.do"

* Load Scripts
do "s03_data_collection.do"
do "s04_preprocessing.do"
do "s05_modeling.do"
do "s06_visualization.do"

* Run data collection
s03_data_collection_main

* Run preprocessing
s04_preprocessing_main

* Run modeling
s05_modeling_main

* Run visualization
s06_visualization_main
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_get_stata_dependencies(folder_path,file_name):

    extension = ".do"
    content = r"""{% raw %}capture program drop get_dependencies
program define get_dependencies
    version 14

    * Accept optional folder path and output file name
    syntax [anything(name=folder_path)] [anything(name=file_name)]

    * Set defaults
    if "`folder_path'" == "" {
        local folder_path "`c(pwd)'"
    }
    if "`file_name'" == "" {
        local file_name "dependencies.txt"
    }

    * Ensure folder exists
    if (fileexists("`folder_path'") == 0) {
        di as error "The specified folder does not exist."
        exit 198
    }

    * Initialize
    local folders "`folder_path'"
    local do_files
    local datasets
    local includes
    local packages
    local checked_files

    * Recursively collect .do files
    while "`folders'" != "" {
        gettoken current_folder folders : folders

        local found_files : dir "`current_folder'" files "*.do", respectcase
        foreach file of local found_files {
            local fullpath "`current_folder'/`file'"
            local do_files `"`do_files' `fullpath'"'
            local checked_files `"`checked_files' `fullpath'"'
        }

        local subdirs : dir "`current_folder'" dirs "*", respectcase
        foreach sub of local subdirs {
            local folders `"`folders' `current_folder'/`sub'"'
        }
    }

    * Parse .do files
    foreach do_file of local do_files {
        quietly {
            file open myfile using "`do_file'", read
            file read myfile line
            while (r(eof) == 0) {
                local lcline = lower("`line'")
                if strpos("`lcline'", "use ") > 0 {
                    local datasets `"`datasets'`line'' _n'
                }
                if strpos("`lcline'", "include ") > 0 | strpos("`lcline'", "do ") > 0 {
                    local includes `"`includes'`line'' _n'
                }
                if strpos("`lcline'", "ssc install") > 0 | strpos("`lcline'", "net install") > 0 {
                    local packages `"`packages'`line'' _n'
                }
                file read myfile line
            }
            file close myfile
        }
    }

    * Prepare metadata
    local timestamp : display %tcCCYY-NN-DD_HH:MM:SS clock("`c(current_date)' `c(current_time)'", "DMY hms")
    local version = c(version)

    * Write output file
    local output_file "`folder_path'/`file_name'"
    capture file delete "`output_file'"
    file open out using "`output_file'", write text

    file write out "Software version:" _n
    file write out "Stata version `version'" _n _n

    file write out "Timestamp: `timestamp'" _n _n

    file write out "Files checked:" _n
    foreach f of local checked_files {
        file write out "`f'" _n
    }
    file write out _n

    file write out "Dependencies:" _n
    file write out "`packages'" 
    file write out "`includes'"
    file write out "`datasets'"

    file close out
    display as result `"Dependency report saved to: `output_file'"'
end
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)    

def create_install_stata_dependencies(folder_path,file_name):   # FIX ME 
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
    write_script(folder_path, file_name, extension, content)

def create_stata_notebook(folder_path,file_name = "s00_workflow"):
    extension = ".ipynb"

    content = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running All Steps in Order (Stata)"),

        nbf.v4.new_markdown_cell("### Stata Setup"),
        nbf.v4.new_code_cell(
            "import stata_setup\n"
            "stata_setup.config('/work/stata17', 'se')  # Adjust to your Stata installation path"
        ),

        nbf.v4.new_markdown_cell("### Run Data Collection"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do s03_data_collection.do\n"
                             "data_collection_main"),

        nbf.v4.new_markdown_cell("### Run Preprocessing"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do s04_preprocessing.do\n"
                             "preprocessing_main"),

        nbf.v4.new_markdown_cell("### Run Modeling"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do s05_modeling.do\n"
                             "modeling_main"),

        nbf.v4.new_markdown_cell("### Run Visualization"),
        nbf.v4.new_code_cell("%%stata\n"
                             "do s06_visualization.do\n"
                             "visualization_main")
    ]

    content.cells.extend(cells)

    write_script(folder_path, file_name, extension, content)


# SAS

def create_sas_script(folder_path, script_name, purpose):
    extension = ".sas"
    content = f"""
* {purpose} code;

%let base_path = ..;
%let raw_data = &base_path./data/00_raw;
%let interim_data = &base_path./data/01_interim;
%let processed_data = &base_path./data/02_processed;

%macro {script_name}_main();
    %put Running {script_name}...;
%mend {script_name}_main;

%{script_name}_main;
"""
    write_script(folder_path, script_name, extension, content)

def create_sas_main(folder_path,file_name):
    extension = ".sas"
    content =f"""{% raw %}
* Main: Running all steps in order;

* Install dependencies
%include "s01_install_dependencies.sas";

* Load utilities
%include "s02_utils.sas";

* Load Scripts;
%include "s03_data_collection.sas";
%include "s04_preprocessing.sas";
%include "s05_modeling.sas";
%include "s06_visualization.sas";

* Run data collection;
%s03_data_collection_main;

* Run preprocessing;
%s04_preprocessing_main;

* Run modeling;
%s05_modeling_main;

* Run visualization;
%s06_visualization_main;
{% endraw %}
"""
    write_script(folder_path, file_name, extension, content)

def create_get_sas_dependencies(folder_path,file_name): # FIX ME 
    extension = ".m"
    content = r"""{% raw %}     
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
    write_script(folder_path, file_name, extension, content)

def create_install_sas_dependencies(folder_path,file_name): # FIX ME 
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
    write_script(folder_path, file_name, extension, content)

def create_sas_notebook(folder_path,file_name = "s00_workflow"):
    extension = ".ipynb"

    content = nbf.v4.new_notebook()

    cells = [
        nbf.v4.new_markdown_cell("# Workflow: Running All Steps in Order (SAS)"),

        nbf.v4.new_markdown_cell("### SAS Setup (using sas_kernel)"),
        nbf.v4.new_code_cell("%%SAS\n* Ensure SAS kernel is working and paths are correctly set;"),

        nbf.v4.new_markdown_cell("### Load and Run Data Collection"),
        nbf.v4.new_code_cell("%%SAS\n%include 's03_data_collection.sas';\n%data_collection_main;"),

        nbf.v4.new_markdown_cell("### Load and Run Preprocessing"),
        nbf.v4.new_code_cell("%%SAS\n%include 's04_preprocessing.sas';\n%preprocessing_main;"),

        nbf.v4.new_markdown_cell("### Load and Run Modeling"),
        nbf.v4.new_code_cell("%%SAS\n%include 's05_modeling.sas';\n%modeling_main;"),

        nbf.v4.new_markdown_cell("### Load and Run Visualization"),
        nbf.v4.new_code_cell("%%SAS\n%include 's06_visualization.sas';\n%visualization_main;")
    ]

    content.cells.extend(cells)
    write_script(folder_path, file_name, extension, content)



@ensure_correct_kernel
def main():

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    # Create scripts and notebook
    create_scripts(load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

    
if __name__ == "__main__":

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()