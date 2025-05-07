import os
import json
import re
import os
import json
import pathlib
import platform

from .general_tools import *

pip_installer(required_libraries =  ['pyyaml','requests','pathspec'])

import yaml
import requests
import pathspec

# Determine file extension based on programming language
ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}

# README.md
def creating_readme(programming_language = "None"):

    # Create and update README and Project Tree:
    file_descriptions = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./file_descriptions.json"))
    update_file_descriptions(programming_language,"./README.md", json_file=file_descriptions)

    generate_readme(programming_language,"./README.md")

    ignore_list = read_treeignore()
    #ignore_list = ["bin",".git",".datalad",".gitkeep",".env","__pycache__","utils"]
   
    create_tree("./README.md",ignore_list ,file_descriptions)
    
def generate_readme(programming_language,readme_file = None):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """
    
    def set_project():

        os_type = platform.system().lower()
        if os_type == "windows":
            usage = (
                "\n**Activate on Windows (PowerShell)**\n\n"
                "```powershell\n"
                "./activate.ps1\n"
                "```\n"
                "\n**Deactivate on Windows (PowerShell)**\n\n"
                "```powershell\n"
                "./deactivate.ps1\n"
                "```\n"
            )

        elif os_type in ("darwin", "linux"):
            usage = (
                "\n**Activate on Linux/macOS (bash)** \n\n"
                "```bash\n"
                "source activate.sh\n"
                "```\n"
                "\n**Deactivate on Linux/macOS (bash)** \n\n"
                "```bash\n"
                "source deactivate.sh\n"
                "```\n"
            )
        return usage

    def set_setup(programming_language,py_version,software_version,conda_version,pip_version,repo_name, repo_user, code_repo):            
        setup = ""

        if repo_name and repo_user:
            setup += "### Clone the Project Repository\n"
            "This will donwload the repository to your local machine. '.env' file is not include in the online repository.\n"
            "Clone the repository using the following command:\n"
            setup += "```\n"
            if code_repo.lower() in ["github","gitlab"]:
                web_repo = code_repo.lower()
                setup += (f"git clone https://{web_repo}.com/{repo_user}/{repo_name}.git\n"   
                        "```\n")
        setup += ("### Navigate to the Project Directory\n"
                "Change into the project directory:\n"  
                "```\n"
                f"cd {repo_name}\n"
                "```\n")

        setup += "### Software Installation\n"
        setup += "The primary method for setting up this project's environment is by using the provided setup script:\n\n"
        setup += "#### Recommended: Using the Custom Setup Script *(currently under development)*\n"

        if programming_language.lower() == "r":
            setup += f"Run the following command to automatically install all {py_version} and {software_version} dependencies:\n\n"
        else: 
            setup += f"Run the following command to automatically install all {py_version} dependencies:\n\n"
        setup += ("```\n"
                "python setup/run_setup.pyn\n"
                "```\n")    
        if programming_language.lower() in ["matlab","stata","sas"]:
            setup +=f"These methods do **not** install external the proprietary software **{software_version}**."
        setup += "If you prefer to install dependencies manually, the following options are available:\n\n"
        
        setup += "#### Install with Conda:\n"
        setup += f"Install the required dependencies using **{conda_version}** and the provided `environment.yml` file:\n"
        setup += "```\n"
        setup += "conda env create -f environment.yml\n"
        setup += "```\n\n"

        if programming_language.lower() == "r":
            setup += f"> ⚡ Note: The `environment.yml` file will also install **{software_version}** alongside Python packages.\n\n"

        setup += "#### Install using Pip:\n"
        setup += f"Alternatively, you can install the Python dependencies using **{py_version}** and **{pip_version}** and the provided`requirements.txt`:\n"
        setup += "```\n"
        setup += "pip install -r requirements.txt\n"
        setup += "```\n\n"
        if programming_language.lower() == "r":
            setup += f"> ⚡ Note: Pip installation will **not** install **{software_version}**.\n\n"
        
        setup += "#### Install the `setup` package:\n"
        setup += "If you installed dependencies manually using Conda or Pip, you must also install the local `setup` package used for configuration and automation scripts:\n"
        setup += "```\n"
        setup += "cd setup\n"
        setup += "pip install -e .\n"
        setup += "cd ..\n"
        setup += "```\n"
        setup += "This makes CLI tools such as `run-setup`, `update-readme`, and `set-dataset` available in your environment.\n\n"

        if programming_language.lower() == "r":
            setup += "#### Install R dependencies using renv:\n\n"
            setup += f"The project's environment is based on **{software_version}**. R package dependencies can be installed using the `renv` package and the provided lock file (`renv.lock`):\n\n"
            setup += "```\n"
            setup += "Rscript -e \"renv::restore()\"\n"
            setup += "```\n\n"
            setup += f"> ⚠️ Warning: Ensure you are using **{software_version}** for full compatibility. If `renv` is not already installed, run `install.packages('renv')` first.\n\n"

        return setup

    def set_contact(authors, orcids, emails):
        contact = ""
        if authors:
            contact += f"**Name:** {authors}\n\n"
        if orcids:
            contact += f"**ORCID:** {orcids}\n\n"
        if emails:
            contact += f"**Email:** {emails}\n\n"
        
        return contact

    def set_script_structure(programming_language,software_version):
        """
        Generate the README section for Script Structure and Usage based on the programming language.

        Args:
            programming_language (str): One of ['r', 'python', 'stata', 'matlab', 'sas']

        Returns:
            str: Formatted README section
        """

        programming_language = programming_language.lower()

        if programming_language not in ["r", "python", "stata", "matlab", "sas"]:
            raise ValueError("Supported programming languages are: r, python, stata, matlab, sas.")

        # Language-specific syntax settings
        if programming_language == "r":
            main_syntax = "::main()"
            comment_prefix = "#"
            source_cmd = "source('"
            source_ext = ".R')"
            notebook_ext = "Rmd"
        elif programming_language == "python":
            main_syntax = ".main()"
            comment_prefix = "#"
            source_cmd = "import "
            source_ext = ""
            notebook_ext = "ipynb"
        elif programming_language == "stata":
            main_syntax = "_main"
            comment_prefix = "*"
            source_cmd = "do "
            source_ext = ".do"
            notebook_ext = "ipynb"
        elif programming_language == "matlab":
            main_syntax = "_main()"
            comment_prefix = "%"
            source_cmd = "run('"
            source_ext = ".m')"
            notebook_ext = "ipynb / mlx"
        elif programming_language == "sas":
            main_syntax = "_main"
            comment_prefix = "*"
            source_cmd = "%include \""
            source_ext = ".sas\";"
            notebook_ext = "ipynb"

        # Build the README text
        structure_usage = f"""The project is written in **{software_version}** and includes modular scripts for standardized data science workflows, organized under `src/`.

Each script is structured to:
- Define a `main()` function for execution
- Set up project paths automatically (raw, interim, processed, results)
- Remain passive unless the `main()` is explicitly called

The typical workflow includes the following steps:

0. **Install Dependencies** — Ensures all required packages/libraries are installed.
1. **Load Utilities** — Loads helper functions used by other scripts (not a pipeline step).
2. **Data Collection** — Imports or generates datasets, stored in `data/raw/`.
3. **Preprocessing** — Cleans and transforms the raw data, outputting to `data/interim/`.
4. **Modeling** — Trains and evaluates machine learning models using processed data. Results saved to `data/processed/`.
5. **Visualization** — Produces plots and visual summaries, saved to `results/figures/`.

> 🛠️ **Note:** `utils` does not define a `main()` function and should not be executed directly.

### Execution Options

You can execute the entire pipeline either by:

**A. Running the `src/main.{source_ext}` orchestration script:**

```
{comment_prefix} Install dependencies
{source_cmd}install_dependencies{source_ext}
    
{comment_prefix} Load scripts
{source_cmd}data_collection{source_ext}
{source_cmd}preprocessing{source_ext}
{source_cmd}modeling{source_ext}
{source_cmd}visualization{source_ext}
{source_cmd}utils{source_ext}

{comment_prefix} Run main functions
data_collection{main_syntax}
preprocessing{main_syntax}
modeling{main_syntax}
visualization{main_syntax}
```

**B. Opening the notebook interface:**  
A pre-built notebook `workflow.{notebook_ext}` is available in the project root.  
This notebook provides the same logic as the main script, but interactively via Jupyter or RMarkdown (depending on the language).

Use this notebook for:

- Exploratory analysis  
- Teaching/demonstration  
- Step-by-step debugging

### Output Paths

| Step             | Output Directory          |
|------------------|----------------------------|
| Data Collection  | `data/raw/`                 |
| Preprocessing    | `data/interim/`             |
| Modeling         | `data/processed/`           |
| Visualization    | `results/figures/`          |

All scripts use relative paths based on their location, ensuring portability and reproducibility across systems.
"""

        return structure_usage

    def set_config_table(programming_language):

        if programming_language.lower() != "r":
            config = """The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.
| File                    | Purpose                                                                                         |
|-------------------------|-------------------------------------------------------------------------------------------------|
| `.gitignore`            | Excludes unnecessary files from Git version control                                             |
| `.rcloneignore`         | Excludes files from syncing when using Rclone                                                   |
| `.treeignore`           | Filters out files/folders from project tree utilities                                           |
| `.cookiecutter`         | Contains metadata for cookiecutter project templates                                            |
| `.env`                  | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `environment.yml`       | Conda environment definition for Python/R, including packages and versions                      |
| `requirements.txt`      | Pip-based Python dependencies for lightweight environments                                      |
| `file_descriptions.json`| Stores structured metadata used to describe and annotate the project directory tree; consumed by setup and documentation tools |
""" 
        else:
            config = """The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.

| File                    | Purpose                                                                                         |
|-------------------------|-------------------------------------------------------------------------------------------------|
| `.gitignore`            | Excludes unnecessary files from Git version control                                             |
| `.rcloneignore`         | Excludes files from syncing when using Rclone                                                   |
| `.treeignore`           | Filters out files/folders from project tree utilities                                           |
| `.cookiecutter`         | Contains metadata for cookiecutter project templates                                            |
| `.env`                  | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `environment.yml`       | Conda environment definition for Python/R, including packages and versions                      |
| `requirements.txt`      | Pip-based Python dependencies for lightweight environments                                      |
| `renv.lock`             | Records the exact versions of R packages used in the project                                    |
| `file_descriptions.json`| Stores structured metadata used to describe and annotate the project directory tree; consumed by setup and documentation tools |
""" 
        return config

    def set_cli_tools():
        cli_tools = """
The `setup` Python package provides a collection of command-line utilities to support project configuration, dependency management, documentation, and reproducibility workflows.

> ℹ️ **Note**: To use these commands, you must first install the local `setup` package.  
> Refer to the [Installation](#installation) section for details on how to install it using `pip install -e .` from the `setup/` directory.

After installing the setup package, the following commands become available from the terminal:


| Command                  | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| `run-backup`             | Executes a full project backup using preconfigured rules and paths.                         |
| `set-dataset`            | Initializes or registers datasets for use in the project (e.g., adds metadata or links).    |
| `update-dependencies`    | Retrieves current dependencies required by the project `./setup` and `./src`.               |
| `run-setup` (in progress)| Main entry point to initialize or reconfigure the project environment.                      |
| `update-readme`          | Automatically updates the main `README.md` file with current metadata and structure.        |
| `reset-templates`        | Resets or regenerates the code templates for `./src`.                                       |
| `code-examples`          | Generates example code and notebooks for supported languages (Python, R, SAS, etc.).        |
| `dcas-migrate`(in progress)| Migrates and validates the project structure for DCAS (Data and Code Availability Standard) compliance.|

### 🛠️ Usage

After activating your environment, run commands like:

```
run-setup
set-dataset
update-requirements
```
"""
        return cli_tools
    
    def set_dcas():
        dcas = """To create a replication package that adheres to the [DCAS (Data and Code Sharing) standard](https://datacodestandard.org/), follow the guidelines ([AEA Data Editor's guidance](https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html)) provided by the Social Science Data Editors. This ensures your research code and data are shared in a clear, reproducible format.

The following are examples of journals that endorse the Data and Code Availability Standard:

- [American Economic Journal: Applied Economics](https://www.aeaweb.org/journals/applied-economics)
- [Econometrica](https://www.econometricsociety.org/publications/econometrica)
- [Economic Inquiry](https://onlinelibrary.wiley.com/journal/14680299)
- [Journal of Economic Perspectives](https://www.aeaweb.org/journals/jep)

For a full list of journals, visit [here](https://datacodestandard.org/journals/).

Individual journal policies may differ slightly. To ensure full compliance, check the policies and submission guidelines of the journal."""
        return dcas
    
    if readme_file is None:
        readme_file = "./README.md"

    readme_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    if os.path.exists(readme_file):
        return
    
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")
    emails = load_from_env("EMAIL",".cookiecutter")
    repo_user = load_from_env(f"{code_repo}_USER")
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION",".cookiecutter")
    py_manager = load_from_env("PYTHON_ENV_MANAGER",".cookiecutter")

    py_version = get_version("python")
    software_version = get_version(programming_language)
    conda_version = get_version("conda") if py_manager.lower() == "conda" else "conda"
    pip_version = get_version("pip")
    install = set_setup(programming_language,py_version,software_version,conda_version,pip_version,repo_name, repo_user, code_repo)
    activate = set_project()
    contact = set_contact(authors, orcids, emails)
    usage = set_script_structure(programming_language,software_version)
    config = set_config_table(programming_language)
    cli_tools = set_cli_tools()
    dcas = set_dcas()

    # Project header
    header = f"""# {project_name}

{project_description}

## 📇 Contact Information

{contact}

<details>
<summary>📋 System and Environment Information</summary>

The project was developed and tested on the following operating system:

- **Operating System**: {platform.platform()}

The environments were set up using:

- **Project setup scripts** (`./setup`) installed with **{py_version}**
- **Project code** (`./src`) installed with **{software_version}**

For further details can be found in the [Installation](#installation) section"

</details>

<details>
<summary>🚀 Project Activation</summary>


To configure the project's environment—including project paths, environment variables, and virtual environments—follow the steps below. These configurations are defined in the `.env` file.

> ⚠️ The `.env` file is excluded from this repository for security reasons. To replicate the environment, please follow the instructions in the [Installation](#installation) section.

{activate}

</details>

<details>
<summary>🔧 CLI Tools</summary>


{cli_tools}

</details>

<details>
<summary>🗂️ Configuration Files (Root-Level)</summary>


{config}

</details>

<details>
<summary>💻 Installation</summary>


Follow these steps to set up the project on your local machine:

{install}

</details>

<details>
<summary>📜 Script Structure and Usage</summary>


{usage}

</details>

<details>
<summary>📦 Dataset List</summary>


To set up or configure a dataset, run the following command:

```
set-dataset
```

**The following datasets are included in the project:**

| Name             | Location        |Hash                       | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Citation               | License               | Notes                  |
|------------------|-----------------|---------------------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|-----------------------|------------------------|

</details>

<details>
<summary>📁 Project Directory Structure</summary>


The current repository structure is shown in the tree below, and descriptions for each file can be found or edited in the `./file_descriptions.json` file.

```

```

</details>

<details>
<summary>📚 Creating a Replication Package Based on DCAS</summary>


{dcas}

</details>

"""

    # Write the README.md content
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write(header)
    print(f"README.md created at: {readme_file}")

# Project Tree
def read_treeignore(file_path=".treeignore"):
    """Load ignore rules from a .gitignore-style file."""
    file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(file_path))

    with open(file_path, "r", encoding="utf-8") as f:
        patterns = f.read().splitlines()
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    return spec

def read_treeignore_old(file_path=".treeignore"):
    """
    Reads the .treeignore file and returns a list of ignored paths.
    
    Parameters:
    file_path (str): Path to the .treeignore file (default is ".treeignore").
    
    Returns:
    list: A list of ignored paths from the .treeignore file.
    """
    ignore_list = []
    file_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(file_path))

    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Strip leading/trailing whitespace and ignore empty lines or comments
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_list.append(line)
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Returning empty ignore list.")
    
    return ignore_list

def create_tree(readme_file=None, ignore_list=None, json_file="./file_descriptions.json", root_folder=None):
    """
    Updates the "Project Tree" section in a README.md file with the project structure.

    Parameters:
    - readme_file (str): The README file to update. Defaults to "README.md".
    - ignore_list (list): Files or directories to ignore.
    - file_descriptions (dict): Descriptions for files and directories.
    - root_folder (str): The root folder to generate the tree structure from. Defaults to the current working directory.
    """

    def generate_tree(folder_path, file_descriptions, ignore_spec=None, prefix="", root_path=None):
        """
        Recursively generates a tree structure of the folder, respecting ignore rules.

        Parameters:
        - folder_path (str): The current folder path.
        - file_descriptions (dict): Optional descriptions for files.
        - ignore_spec (PathSpec): PathSpec object for ignore rules.
        - prefix (str): The prefix for the current level of the tree.
        - root_path (str): The root path of the project, needed for correct relative paths.
        """
        if root_path is None:
            root_path = folder_path  # First call: set root path
        
        tree = []
        items = sorted(os.listdir(folder_path))
        for index, item in enumerate(items):
            item_path = os.path.join(folder_path, item)

            # Correct: compute rel_path relative to root
            rel_path = os.path.relpath(item_path, start=root_path).replace("\\", "/")  # Always use forward slashes

            if ignore_spec and ignore_spec.match_file(rel_path):
                continue

            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if file_descriptions and item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}")

            if os.path.isdir(item_path):
                child_prefix = f"{prefix}   " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, file_descriptions, ignore_spec=ignore_spec, prefix=child_prefix, root_path=root_path))

        return tree

    def update_readme_tree_section(readme_file, root_folder, file_descriptions, ignore_list):
        # Read the entire README content into lines
        with open(readme_file, "r", encoding="utf-8") as file:
            readme_content = file.readlines()

        start_index = None
        end_index = None

        # Step 1: Find the <summary> line for Project Directory Structure
        for i, line in enumerate(readme_content):
            if "<summary>" in line and "Project Directory Structure" in line:
                # Step 2: From there, find the next line with just ```
                for j in range(i + 1, len(readme_content)):
                    if readme_content[j].strip() == "```":
                        start_index = j + 1  # Start *after* opening ```
                        break
                break  # Stop after the first <summary> match

        if start_index is None:
            print("❌ Could not find project directory summary section with code block. No changes made.")
            return

        # Step 3: Find the closing ```
        for k in range(start_index, len(readme_content)):
            if readme_content[k].strip() == "```":
                end_index = k
                break

        if end_index is None:
            print("❌ No closing ``` found for the project tree block. No changes made.")
            return

        # Step 4: Generate the updated tree structure
        tree_structure = generate_tree(
            folder_path=root_folder,
            file_descriptions=file_descriptions,
            ignore_spec=ignore_list,
            root_path=root_folder
        )

        # Step 5: Replace old tree block with the new one
        updated_content = (
            readme_content[:start_index] +                        # Before tree block
            [line + "\n" for line in tree_structure] +            # New tree lines
            readme_content[end_index:]                            # After closing ```
        )

        # Step 6: Write the updated README
        with open(readme_file, "w", encoding="utf-8") as file:
            file.writelines(updated_content)

        print("✅ README updated with new project directory tree.")

    json_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_file))

    if not readme_file:
        readme_file = "README.md"
    
    readme_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    if not os.path.exists(readme_file):
        print(f"README file '{readme_file}' does not exist. Exiting.")
        return

    if not root_folder:
        root_folder = str(pathlib.Path(__file__).resolve().parent.parent.parent)
    else:
        root_folder = os.path.abspath(root_folder)

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided


    if isinstance(json_file, str) and json_file.endswith(".json") and os.path.exists(json_file): 
        with open(json_file, "r", encoding="utf-8") as json_file:
            file_descriptions = json.load(json_file)
    else:
        file_descriptions = None
    
    update_readme_tree_section(readme_file, root_folder, file_descriptions, ignore_list)
    
def update_file_descriptions(programming_language, readme_file = "README.md", json_file="./file_descriptions.json"):
    """
    Reads the project tree from an existing README.md and updates a file_descriptions.json file.

    Parameters:
    - readme_file (str): Path to the README.md file.
    - json_file (str): The name of the JSON file for file descriptions.

    Returns:
    - None
    """

    def create_file_descriptions(programming_language,json_file):

        def src_file_descriptions(programming_language):

            src_template = {
                "data_collection": "Script to collect and import raw data from external sources.",
                "get_dependencies": "Checks and retrieves necessary {language} package dependencies.",
                "install_dependencies": "Installs any missing {language} packages required for the project.",
                "main": "The entry point script that orchestrates the workflow of the project.",
                "modeling": "Defines the process for building and training models using the data.",
                "preprocessing": "Handles data cleaning and transformation tasks.",
                "utils": "Contains helper functions for common tasks throughout the project.",
                "visualization": "Generates visual outputs such as charts, graphs, and plots."
            }
            

            file_extension = ext_map.get(programming_language.lower(), "txt")  # Default to "txt" if language is unknown

            # Generate the descriptions by replacing placeholders in the template
            descriptions = {}
            for key, description in src_template.items():
                file_name = f"{key}.{file_extension}"  # Create the file name with the correct extension
                descriptions[file_name] = description.format(language=programming_language)

            return descriptions


        file_descriptions = {

            # Directories
            "data": "Directory containing scripts to download or generate data.",
            "external": "Directory for externally sourced data from third-party providers.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "src": "Directory containing source code for use in this project.",
            "docs": "Directory for documentation files, reports, or rendered markdown.",
            "notebooks": "Directory for Jupyter or R notebooks for exploratory and explanatory work.",
            "results": "Directory for generated results from the project, such as models, logs, or summaries.",
            "setup": "Directory containing the local Python package used for configuring and initializing the project environment.",
            "DCAS template": "Directory containing a 'replication package' template for the DCAS (Data and Code Sharing) standard.",
            "utils": "Python module within the setup package containing utility scripts and functions used by CLI tools.",

            # Setup and configuration files
            ".cookiecutter": "Cookiecutter template configuration for creating new project structures.",
            ".gitignore": "Specifies files and directories that should be ignored by Git.",
            ".rcloneignore": "Specifies files and directories that should be excluded from remote sync via Rclone.",
            ".treeignore": "Defines files or folders to exclude from file tree utilities or visualizations.",
            ".gitlog": "Git log output file for tracking changes to the repository over time.",
            ".env": "Environment-specific variables such as paths, tokens, or secrets. Typically excluded from version control.",
            "CITATION.cff": "Citation metadata file for academic attribution and scholarly reference.",
            "file_descriptions.json": "Structured JSON file used to describe and annotate the project directory tree.",
            "LICENSE.txt": "The project's license file, outlining terms and conditions for usage and distribution.",
            "README.md": "The project README for this project.",
            #"README.md": "Template README file aligned with DCAS guidelines for social science replication packages.",
            "requirements.txt": "The requirements file for installing Python dependencies via pip.",
            "environment.yml": "Conda environment definition file for installing R and Python dependencies.",
            "renv.lock": "Lockfile used by the R `renv` package to capture the exact state of the R environment for reproducibility.",

            # Setup package scripts
            "deic_storage_download.py": "Script to download data from DEIC storage for the project.",
            "dependencies.txt": "Plain text list of external Python dependencies for installation.",
            "get_dependencies.py": "Retrieves and checks required dependencies for the project environment.",
            "install_dependencies.py": "Installs any missing dependencies listed in `dependencies.txt` or detected dynamically.",
            "readme_templates.py": "Generates README templates for various environments or publication formats.",
            "set_raw_data.py": "Script to prepare and stage raw data for initial project use.",
            "setup.ps1": "PowerShell script to initialize environment setup on Windows systems.",
            "setup.py": "Defines the setup package and registers CLI tools; enables pip installation (`pip install -e .`).",
            "setup.sh": "Bash script to initialize environment setup on Linux/macOS systems.",
            "update_requirements.py": "Updates the `requirements.txt` file based on currently installed packages.",
            "utils.py": "Contains shared utility functions used throughout the `setup` package and CLI tools."
        }


        if programming_language:
            # Update the existing dictionary with the new descriptions
            file_descriptions.update(src_file_descriptions(programming_language))

        # Save to JSON file
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(file_descriptions, file, indent=4, ensure_ascii=False)

        return file_descriptions

    def update_file_descriptions(json_file,readme_file):
        
        if not os.path.exists(readme_file):
            return
        # Read the README.md and extract the "Project Tree" section
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()


        # Extract the project tree section using regex
        #tree_match = re.search(r"##\s*Project Directory Structure\s*\n+([\s\S]+?)```", readme_content)
        tree_match = re.search(r"<summary>\s*📁\s*Project Directory Structure\s*</summary>\s*([\s\S]+?)```", readme_content)
        if not tree_match:
            print("'📁 Project Directory Structure' section not found in README.md")
            return

        project_tree = tree_match.group(1)

        # Extract file descriptions from the project tree
        tree_lines = project_tree.splitlines()
        for line in tree_lines:
            while line.startswith("│   "):
                line = line[4:]  # Remove prefix (4 characters)
            match = re.match(r"^\s*(├──|└──|\|.*)?\s*(\S+)\s*(<- .+)?$", line)
            if match:
                filename = match.group(2).strip()
                description = match.group(3)  # This captures everything after '<-'
                if description:
                    description = description.strip()[3:]  # Remove the '<- ' part and get the description text
                if description:
                    file_descriptions[filename] = description

        # Write the updated descriptions to the JSON file
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(file_descriptions, f, indent=4, ensure_ascii=False)

        print(f"File descriptions updated in {json_file}")

    json_file   = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(json_file))
    readme_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            file_descriptions = json.load(f)
    else:
        file_descriptions = create_file_descriptions(programming_language,json_file)

    update_file_descriptions(json_file,readme_file)

# Dataset Table
def generate_dataset_table(json_file_path):
    """
    Generates a markdown table based on the data in a JSON file.

    Parameters:
        json_file_path (str): Path to the JSON file containing dataset metadata.

    Returns:
        str: A markdown formatted table as a string.
    """
    
    # Check if the JSON file exists
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file {json_file_path} does not exist.")
    
    # Read the JSON file
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    # If the data is a list, loop through each dataset entry
    if isinstance(data, list):
        markdown_table = (
            f"| Name             | Location        |Hash                       | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Citation               | License               | Notes                  |\n"
            f"|------------------|-----------------|---------------------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|-----------------------|------------------------|\n"
        )

        full_table = (
            f"| Name             | Files                             |Hash                       | Location        | Provided        | File Size (MB) | Run Command               | Source           | DOI             | Citation               | License               | Notes                |\n"
            f"|------------------|-----------------------------------|---------------------------|-----------------|-----------------|----------------|---------------------------|------------------|-----------------|------------------------|-----------------------|----------------------|\n"
        )

        for entry in data:
            if isinstance(entry, dict):  # Only process dictionary entries
                # Extract required information from the JSON data
                data_name = entry.get("data_name", "N/A")
                data_files = " ; ".join(entry.get("data_files", ["Not available"]))  # Newline separated
                data_sizes = " ; ".join(str(size) for size in entry.get("data_size", ["Not available"]))
                location = entry.get("destination", "N/A")
                hash = entry.get("hash", "N/A")
                provided = "Provided" if entry.get("data_files") else "Can be re-created"
                run_command = entry.get("run_command", "N/A")
                number_of_files = entry.get("number_of_files", 0)
                total_size_mb = entry.get("total_size_mb", 0)
                file_formats = "; ".join(entry.get("file_formats", ["Not available"]))
                source = entry.get("source", "N/A")
                doi = entry.get("DOI", "Not provided")
                citation = entry.get("citation", "Not provided")
                license = entry.get("license", "Not provided")
                notes = entry.get("notes", "No additional notes")


                 # Format pdf table
                data_files = entry.get("data_files", ["Not available"])
                for file, size in zip(data_files, data_sizes):
                    full_table += (f"|{data_name}|{file}|{hash}|{location}|{provided}|{size}|{run_command}|{source}|{doi}|{citation}|{license}|{notes}|\n")

                # Format the markdown table for this entry
                markdown_table += (f"|{data_name}|{location}|{hash}|{provided}|{run_command}|{number_of_files}|{total_size_mb}|{file_formats}|{source}|{doi}|{citation}|{license}|{notes}|\n")
       
        return markdown_table,full_table
    else:
        # If the data is not a list, raise an error
        raise TypeError(f"Expected a list of datasets but got {type(data)}.")

def dataset_to_readme(markdown_table: str, readme_file: str = "./README.md"):
    """
    Updates or appends the '## Dataset List' section in the README file.

    Parameters:
        markdown_table (str): The markdown table to insert.
        readme_file (str): Path to the README file.
    """
    section_title = "**The following datasets are included in the project:**"

    new_dataset_section = f"{section_title}\n\n{markdown_table.strip()}\n"


    if not readme_file:
        readme_file = "README.md"
    
    readme_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

    try:
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()

        if section_title in readme_content:
            # Find the start and end of the existing section
            start = readme_content.find(section_title)
            end = readme_content.find("\n## ", start + len(section_title))
            if end == -1:
                end = len(readme_content)
            updated_content = readme_content[:start] + new_dataset_section + readme_content[end:]
        else:
            # Append the new section at the end
            updated_content = readme_content.strip() + "\n\n" + new_dataset_section

    except FileNotFoundError:
        # If the README doesn't exist, create it with the new section
        updated_content = new_dataset_section

    # Write the updated content to the README file
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(updated_content.strip())

    print(f"{readme_file} successfully updated with dataset section.")


# CITATION.cff
def create_citation_file(project_name, version, authors, orcids, code_repo, doi=None, release_date=None):
    """
    Create a CITATION.cff file based on inputs from cookiecutter.json and environment variables for URL.

    Args:
        project_name (str): Name of the project.
        version (str): Version of the project.
        authors (str): Semicolon-separated list of author names.
        orcids (str): Semicolon-separated list of ORCID IDs corresponding to the authors.
        code_repo (str): Either "GitHub" or "GitLab" (or None).
        doi (str): DOI of the project. Optional.
        release_date (str): Release date in YYYY-MM-DD format. Defaults to empty if not provided.
    """
    # Split authors and ORCIDs into lists
    #author_names = authors.split(";") if authors else []
    #orcid_list = orcids.split(";") if orcids else []
    author_names = re.split(r'[;,]', authors) if authors else []
    orcid_list = re.split(r'[;,]', orcids) if orcids else []

    # Create a structured list of author dictionaries
    author_data_list = []
    for i, name in enumerate(author_names):
        name = name.strip()
        if not name:
            continue  # Skip empty names
        
        name_parts = name.split(" ")
        if len(name_parts) == 1:
            # If only a given name is provided
            given_names = name_parts[0]
            family_names = ""
        else:
            given_names = " ".join(name_parts[:-1])
            family_names = name_parts[-1]
        
        author_data = {"given-names": given_names}
        if family_names:
            author_data["family-names"] = family_names

        # Add ORCID if available
        if i < len(orcid_list):
            orcid = orcid_list[i].strip()
            if orcid:
                if not orcid.startswith("https://orcid.org/"):
                    orcid = f"https://orcid.org/{orcid}"
                author_data["orcid"] = orcid

        author_data_list.append(author_data)

    # Generate URL based on version control
    if code_repo.lower() == "github":
        user = load_from_env(["GITHUB_USER"])
        repo = load_from_env(["GITHUB_REPO"])
        base_url = "https://github.com"
    elif code_repo.lower() == "gitlab":
        user = load_from_env(["GITLAB_USER"])
        repo = load_from_env(["GITLAB_REPO"])
        base_url = "https://gitlab.com"
    else:
        user = None
        repo = None
        base_url = None

    if user and repo and base_url:
        url = f"{base_url}/{user}/{repo}"
    else:
        url = ""

    # Build the citation data
    citation_data = {
        "cff-version": "1.2.0",
        "title": project_name,
        "message": "If you use this software, please cite it as below.",
        "version": version,
        "authors": author_data_list,
        "doi": doi if doi else "",
        "date-released": release_date if release_date else "",
        "url": url,
    }

    # Write to CITATION.cff
    file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("CITATION.cff"))
    with open(file, "w") as cff_file:
        yaml.dump(citation_data, cff_file, sort_keys=False)

# Download Readme template:
def download_README_template(url:str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md", readme_file:str = "./README_DCAS_template.md"):
    
    readme_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(readme_file))

     # Check if the local file already exists
    if os.path.exists(readme_file):
        return
    
    # Ensure the parent directory exists
    folder_path = os.path.dirname(readme_file)
    os.makedirs(folder_path, exist_ok=True)

    # Send GET request to the raw file URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content to a file
        with open(readme_file, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download {readme_file} from {url}")

def main():
    creating_readme(programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

if __name__ == "__main__":
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()
