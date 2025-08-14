from __future__ import annotations
import os
import json
import re
import pathlib
import platform
from typing import List
import pathspec


from .readme_sections import *
from .set_dataset import generate_dataset_table, dataset_to_readme

package_installer(required_libraries =  ['pyyaml','requests'])

import yaml
import requests


def merge_pathspecs(spec_a: pathspec.PathSpec,
                    spec_b: pathspec.PathSpec,
                    style: str = "gitwildmatch",
                    dedupe: bool = True) -> pathspec.PathSpec:
    # Pull the raw pattern text out of each compiled Pattern
    patterns = [p.pattern for p in getattr(spec_a, "patterns", [])] + \
               [p.pattern for p in getattr(spec_b, "patterns", [])]

    if dedupe:
        seen = set()
        patterns = [x for x in patterns if not (x in seen or seen.add(x))]

    return pathspec.PathSpec.from_lines(style, patterns)

def datasets_ignore(
    datasets_json: str | pathlib.Path,
    base: str | pathlib.Path | None = None,
) -> pathspec.PathSpec:
    """
    Read datasets.json and build a gitwildmatch PathSpec containing ONLY
    directory destinations. Patterns are:
      - relative to `base` (if provided)
      - forward-slashed
      - guaranteed to end with "/"
      - deduplicated (order-preserving)
    """
    def _to_dir_pattern(p: str | pathlib.Path, base: str | pathlib.Path | None) -> str:
        p = pathlib.Path(p)
        if base is not None:
            base = pathlib.Path(base).resolve()
            p = (base / p).resolve().relative_to(base)
        s = p.as_posix()
        if s.startswith("./"):
            s = s[2:]
        if not s.endswith("/"):
            s += "/"
        return s

    datasets_json = pathlib.Path(datasets_json)

    if not os.path.exists(datasets_json):
        return None

    with open(datasets_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    patterns: list[str] = []
    seen: set[str] = set()

    for ds in payload.get("datasets", []):
        dest = str(ds.get("destination", "")).strip()
        if not dest:
            continue
        # treat as directory if it either ends with a separator or has no file extension
        is_dir = dest.endswith(("\\", "/")) or pathlib.Path(dest).suffix == ""
        if not is_dir:
            continue
        pat = _to_dir_pattern(dest, base=base)
        if pat not in seen:
            seen.add(pat)
            patterns.append(pat)

    # Build and return a PathSpec using gitwildmatch
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


# README.md
def creating_readme(programming_language = "None"):

    programming_language = programming_language.lower()

    if ext_map.get(programming_language) is None:
        return f"Unsupported programming language: {programming_language}"

    code_path = language_dirs.get(programming_language)
   
    # Create and update README and Project Tree:
    file_descriptions = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./file_descriptions.json"))
    readme_file= str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./README.md"))
    code_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(code_path))
    
    update_file_descriptions(programming_language, readme_file, file_descriptions)
    generate_readme(readme_file, code_path, file_descriptions)

    markdown_table, _ = generate_dataset_table("./datasets.json")

    if markdown_table:
        dataset_to_readme(markdown_table)
        
    ignore_list, _  = read_toml_ignore(toml_path = "pyproject.toml" ,  ignore_filename = ".treeignore",tool_name = "treeignore",toml_key = "patterns")
    dataset_list = datasets_ignore(datasets_json = "datasets.json")

    if dataset_list:
        ignore_list = merge_pathspecs(ignore_list,dataset_list)
    
    create_tree(readme_file,ignore_list ,file_descriptions)
    
def generate_readme(readme_file = "./README.md", code_path = None,json_file="./file_descriptions.json"):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """
    
    header = main_text(json_file,code_path)

    # Write the README.md content
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write(header)
    print(f"README.md created at: {readme_file}")

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
                child_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                #child_prefix = f"{prefix}   " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, file_descriptions, ignore_spec=ignore_spec, prefix=child_prefix, root_path=root_path))

        return tree

    def update_readme_tree_section(readme_file, root_folder, file_descriptions, ignore_list):
        # Read the entire README content into lines
        with open(readme_file, "r", encoding="utf-8") as file:
            readme_content = file.readlines()

        start_index = None
        end_index = None

        # Step 1: Find the line that starts with ```tree
        for i, line in enumerate(readme_content):
            if line.strip().startswith("```tree"):
                start_index = i + 1  # Line *after* ```tree
                break

        if start_index is None:
            print("❌ Could not find ```tree code block. No changes made.")
            return

        # Step 2: Find the closing ```
        for j in range(start_index, len(readme_content)):
            if readme_content[j].strip() == "```":
                end_index = j
                break

        if end_index is None:
            print("❌ No closing ``` found for the tree block. No changes made.")
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

    if not readme_file:
        readme_file = "README.md"
    
    if not os.path.exists(readme_file):
        print(f"README file '{readme_file}' does not exist. Exiting.")
        return

    if not root_folder:
        root_folder = str(pathlib.Path(__file__).resolve().parent.parent.parent)
    else:
        root_folder = os.path.abspath(root_folder)

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided

    file_descriptions = read_toml_json(folder = root_folder, json_filename =  json_file , tool_name = "file_descriptions", toml_path = "pyproject.toml")

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

        def code_file_descriptions(programming_language):
            # Set extensions based on programming language
            if programming_language.lower() == "r":
                source_ext, notebook_ext = ".R", ".Rmd"
            elif programming_language.lower() == "python":
                source_ext, notebook_ext = ".py", ".ipynb"
            elif programming_language.lower() == "stata":
                source_ext, notebook_ext = ".do", ".ipynb"
            elif programming_language.lower() == "matlab":
                source_ext, notebook_ext = ".m", [".ipynb", ".mlx"]
                notebook_ext = notebook_ext[0]  # Default to .ipynb
            else:  # SAS
                source_ext, notebook_ext = ".sas", ".ipynb"

            code_template = {
                "s00_main": "orchestrates the full pipeline",
                "s00_workflow": "notebook orchestrating the full pipeline",
                "s01_install_dependencies": "installs any missing packages required for the project",
                "s02_utils": "shared helper functions (not directly executable)",
                "s03_data_collection": "imports or generates raw data",
                "s04_preprocessing": "cleans and transforms data",
                "s05_modeling": "fits models and generates outputs",
                "s06_visualization": "creates plots and summaries",
                "get_dependencies": "retrieves and checks required packages for the project (utilised)",

                # Unit tests
                "test_s00_main": "tests the main pipeline orchestration in `s00_main.*`",
                "test_s00_workflow": "tests the full pipeline notebook `s00_workflow{}`".format(notebook_ext),
                "test_s01_install_dependencies": "tests the dependency installation logic in `s01_install_dependencies.*`",
                "test_s02_utils": "tests utility functions defined in `s02_utils.*`",
                "test_s03_data_collection": "tests data import and generation logic from `s03_data_collection.*`",
                "test_s04_preprocessing": "tests data cleaning and transformation in `s04_preprocessing.*`",
                "test_s05_modeling": "tests model fitting and output generation in `s05_modeling.*`",
                "test_s06_visualization": "tests plotting and summary creation in `s06_visualization.*`",
                "test_get_dependencies": "tests the package dependency resolution in `get_dependencies.*`"
            }

            descriptions = {}

            for key, description in code_template.items():
                if key == "s00_workflow":
                    file_name = f"{key}{notebook_ext}"
                elif key == "test_s00_workflow":
                    file_name = f"{key}{notebook_ext}"
                else:
                    file_name = f"{key}{source_ext}"
                descriptions[file_name] = description

            return descriptions

        file_descriptions = {

            # Directories
            "data": "Directory containing scripts to download or generate data.",
            "01_interim": "Intermediate data transformed during the workflow.",
            "02_processed": "The final, clean data used for analysis or modeling.",
            "03_external": "External data sources or files obtained from third parties.",
            "00_raw": "Original, immutable raw data.",
            "figures": "Directory containing generated plots, charts, and visual summaries.",
            "tests": "Directory containing unit tests.",
            "testthat": "Contains unit tests for R scripts using the testthat framework.",
            "src": "Directory containing source code for use in this project.",
            "R": "Directory containing R source code scripts for this project.",
            "stata": "Directory containing Stata scripts for this project.",
            "docs": "Directory for documentation files, reports, or rendered markdown.",
            "notebooks": "Directory for Jupyter or R notebooks for exploratory and explanatory work.",
            "results": "Directory for generated results from the project, such as models, logs, or summaries.",
            "setup": "Directory containing the local Python package used for configuring and initializing the project environment.",
            "DCAS template": "Directory containing a 'replication package' template for the DCAS (Data and Code Sharing) standard.",
            "utils": "Python module within the setup package containing utility scripts and functions used by CLI tools.",
            "renv": "Directory automatically managed by the R `renv` package, containing the project-local R library and metadata files used to restore the environment.",
            "bin": "Directory for executable scripts or binaries used in the project.",
            ".venv": "Project-local Python virtual environment directory created using `python -m venv` or similar tools.",
            ".conda": "Project-local Conda environment directory created using `conda create --prefix` for isolated dependency management.",

            # Setup and configuration files
            ".cookiecutter": "Cookiecutter template configuration for creating new project structures.",
            ".gitignore": "Specifies files and directories that should be ignored by Git.",
            ".rcloneignore": "Specifies files and directories that should be excluded from remote sync via Rclone.",
            ".treeignore": "Defines files or folders to exclude from file tree utilities or visualizations.",
            ".gitlog": "Git log output file for tracking changes to the repository over time.",
            ".env": "Environment-specific variables such as paths, tokens, or secrets. Typically excluded from version control.",
            ".Rprofile": "Startup file for R sessions. Used by `renv` to automatically load the correct project-local R environment when the project is opened.",
            "CITATION.cff": "Citation metadata file for academic attribution and scholarly reference.",
            "file_descriptions.json": "Structured JSON file used to describe and annotate the project directory tree.",
            "platform_rules.json": "Maps Python packages to platform-specific tags (win32, darwin, linux) to conditionally include them in requirements.txt or environment.yml.",
            "LICENSE.txt": "The project's license file, outlining terms and conditions for usage and distribution.",
            "README.md": "The project README for this project.",
            "requirements.txt": "The requirements file for installing Python dependencies via pip.",
            "environment.yml": "Conda environment definition file for installing R and Python dependencies.",
            "renv.lock": "Snapshot file generated by the R `renv` package. Records the exact versions and sources of R packages used in the project to enable precise environment restoration.",
            "uv.lock": "Dependency lock file generated by the uv package manager for reproducible Python environments.",

            # Continuous Integration config files
            ".git": "Version control directory used by Git to manage repository history.",
            ".github": "Defines GitHub Actions workflows for continuous integration and deployment.",
            ".gitlab-ci.yml": "Specifies a GitLab CI/CD pipeline for running tests on one or more custom or shared runners.",
            ".woodpecker.yml": "Configures a Woodpecker CI pipeline used on Codeberg to run test jobs in a Linux environment.",

            # Setup package scripts
            "activate.ps1": "PowerShell script to activate the project's virtual environment on Windows.",
            "deactivate.ps1": "PowerShell script to deactivate the project's virtual environment on Windows.",
            "activate.sh": "Shell script to activate the project's virtual environment on Unix-based systems.",
            "deactivate.sh": "Shell script to deactivate the project's virtual environment on Unix-based systems.",
            "deic_storage_download.py": "Script to download data from Deic-Storage for the project.",
            "dependencies.txt": "Plain text list of external Python dependencies for installation.",
            "get_dependencies.py": "Retrieves and checks required dependencies for the project environment.",
            "install_dependencies.py": "Installs any missing dependencies listed in `dependencies.txt` or detected dynamically.",
            "readme_templates.py": "Generates README templates for various environments or publication formats.",
            "set_raw_data.py": "Script to prepare and stage raw data for initial project use.",
            "setup.ps1": "PowerShell script to initialize environment setup on Windows systems.",
            "pyproject.toml": "Defines the setup package and registers CLI tools; enables pip installation (`pip install -e .`).",
            "setup.sh": "Bash script to initialize environment setup on Linux/macOS systems.",
            "utils.py": "Contains shared utility functions used throughout the `setup` package and CLI tools."
        }

        if programming_language:
            # Update the existing dictionary with the new descriptions
            file_descriptions.update(code_file_descriptions(programming_language))

        write_toml_json(data = file_descriptions, json_filename = json_file, tool_name = "file_descriptions", toml_path = "pyproject.toml")

        return file_descriptions

    def update_descriptions(json_file,readme_file):
        
        if not os.path.exists(readme_file):
            return
        # Read the README.md and extract the "Project Tree" section
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()


        tree_match = re.search(r"```tree\s*([\s\S]+?)```", readme_content)
        if not tree_match:
            print("```tree block not found in README.md")
            return

        project_tree = tree_match.group(1).strip()

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

        write_toml_json(data = file_descriptions, json_filename = json_file, tool_name = "file_descriptions", toml_path = "pyproject.toml")
        
    file_descriptions = read_toml_json(json_filename = json_file, tool_name = "file_descriptions", toml_path = "pyproject.toml")    

    if not file_descriptions:
        file_descriptions = create_file_descriptions(programming_language,json_file)

    update_descriptions(json_file,readme_file)

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
        user = load_from_env("GITHUB_USER")
        repo = load_from_env("GITHUB_REPO")
        hostname = load_from_env('GITHUB_HOSTNAME') or "github.com"
        base_url = f"https://{hostname}"  
    elif code_repo.lower() == "gitlab":
        user = load_from_env("GITLAB_USER")
        repo = load_from_env("GITLAB_REPO")
        hostname = load_from_env('GITHUB_HOSTNAME') or "gitlab.com"
        base_url = f"https://{hostname}"  
    elif code_repo.lower() == "codeberg":
        user = load_from_env("CODEBERG_USER")
        repo = load_from_env("CODEBERG_REPO")
        hostname = load_from_env('CODEBERG_HOSTNAME') or "codeberg.org"
        base_url = f"https://{hostname}"     
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

def update_requirements(programming_language, readme_file):
    
    def write_to_readme(readme_file, code_dependencies):
        # Check if the README file exists; create it if not
        if not os.path.exists(readme_file):
            creating_readme(programming_language=load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter"))

        try:
            with open(readme_file, "r", encoding="utf-8") as file:
                readme_content = file.read()

            # Look for fenced code block labeled 'code_dependencies'
            start_marker = "```code_dependencies"
            end_marker = "```"

            start = readme_content.find(start_marker)
            if start != -1:
                start += len(start_marker)
                end = readme_content.find(end_marker, start)
                if end != -1:
                    # Replace the content in between
                    updated_content = (
                        readme_content[:start].rstrip() + "\n" +
                        code_dependencies.strip() + "\n" +
                        readme_content[end:]
                    )
                else:
                    print("❌ Could not find closing ``` after ```code_dependencies. No changes made.")
                    return
            else:
                # If the block doesn't exist, append a new one
                updated_content = readme_content.strip() + "\n\n```code_dependencies\n" + code_dependencies.strip() + "\n```"

        except FileNotFoundError:
            # If README doesn't exist at all, create with only this block
            updated_content = "```code_dependencies\n" + code_dependencies.strip() + "\n```"

        # Write the updated content to the README
        with open(readme_file, "w", encoding="utf-8") as file:
            file.write(updated_content.strip())

        print(f"{readme_file} successfully updated.")

    code_path = language_dirs.get(programming_language.lower())
    code_dependencies = read_dependencies(str(pathlib.Path(__file__).resolve().parent.parent.parent / f"{code_path}/dependencies.txt"))
   
   
    write_to_readme(readme_file,code_dependencies)

def main():
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    creating_readme(programming_language = programming_language)
    readme_file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./README.md"))
    update_requirements(programming_language, readme_file)

if __name__ == "__main__":
    main()
