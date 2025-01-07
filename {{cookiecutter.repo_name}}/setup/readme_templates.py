import os
import subprocess
import sys
import json
import re
import os
import json
import subprocess
import sys

required_libraries = ['python-dotenv','pyyaml','requests'] 
installed_libraries = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()

for lib in required_libraries:
    try:
        # Check if the library is already installed
        if not any(lib.lower() in installed_lib.lower() for installed_lib in installed_libraries):
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {lib}: {e}")

from dotenv import dotenv_values, load_dotenv
import yaml
import requests

sys.path.append('setup')
from utils import *

# README.md
def creating_readme(repo_name ,project_name, project_description,code_repo,author_name):

    if code_repo.lower() in ["github","gitlab"]:
        web_repo = code_repo.lower()
        setup = f"""git clone https://{web_repo}.com/username/{repo_name}.git"" \
        cd {repo_name} \
        python setup.py"""
    else: 
        setup = f"""cd {repo_name} python setup.py"""
    usage = """python src/workflow.py"""
    contact = f"{author_name}"

    # Create and update README and Project Tree:
    update_file_descriptions("README.md", json_file="FILE_DESCRIPTIONS.json")
    generate_readme(project_name, project_description,setup,usage,contact,"README.md")
    download_and_rename_github_file()
    create_tree("README.md", ['bin','.git','.datalad','.gitkeep','.env','__pycache__'] ,"FILE_DESCRIPTIONS.json")
    
def generate_readme(project_name, project_description,setup,usage,contact,readme_file = None):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """


    # Project header
    header = f"""# {project_name}

{project_description}

## Contact Information
{contact}

## Installation
```
{setup}
```
## Usage
```
{usage}
```
## Dataset list

## Computational requirements

### Software Requirements

## Creating a replication package

https://datacodestandard.org/

https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html

https://social-science-data-editors.github.io/template_README/

## Project Tree
------------

------------
"""
    if readme_file is None:
        readme_file = "README.md" 
    if os.path.exists(readme_file):
        return
    
    # Write the README.md content
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write(header)
    print(f"README.md created at: {readme_file}")

# Project Tree
def create_tree(readme_file=None, ignore_list=None, file_descriptions=None, root_folder=None):
    """
    Updates the "Project Tree" section in a README.md file with the project structure.

    Parameters:
    - readme_file (str): The README file to update. Defaults to "README.md".
    - ignore_list (list): Files or directories to ignore.
    - file_descriptions (dict): Descriptions for files and directories.
    - root_folder (str): The root folder to generate the tree structure from. Defaults to the current working directory.
    """
    def generate_tree(folder_path, prefix="",span_style:bool = True):
        """
        Recursively generates a tree structure of the folder.

        Parameters:
        - folder_path (str): The root folder path.
        - prefix (str): The prefix for the current level of the tree.
        """
        tree = []
        if span_style:
            tree.append('<span style="font-size: 5px;">')
        items = sorted(os.listdir(folder_path))  # Sort items for consistent structure
        for index, item in enumerate(items):
            if item in ignore_list:
                continue
            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if file_descriptions and item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}<br> ") # Add spaces for a line break
            if os.path.isdir(item_path):
                child_prefix = f"{prefix}&nbsp;&nbsp;&nbsp;&nbsp;" if is_last else f"{prefix}│   "
                #child_prefix = f"{prefix}    " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, prefix=child_prefix,span_style=False))
        if span_style:
            tree.append("</span>")
        return tree

    if not readme_file:
        readme_file = "README.md"

    if not os.path.exists(readme_file):
        print(f"README file '{readme_file}' does not exist. Exiting.")
        return

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided


    if isinstance(file_descriptions, str) and file_descriptions.endswith(".json") and os.path.exists(file_descriptions): 
        with open(file_descriptions, "r", encoding="utf-8") as json_file:
            file_descriptions = json.load(json_file)
    else:
        file_descriptions = None

    if not root_folder:
        root_folder = os.getcwd()

    # Read the existing README.md content
    with open(readme_file, "r", encoding="utf-8") as file:
        readme_content = file.readlines()

    # Check for "Project Tree" section
    start_index = None
    for i, line in enumerate(readme_content):
        if "Project Tree" in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
        #if line.strip() == "Project Tree" and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
            start_index = i + 2  # The line after "------------"
            break

    if start_index is None:
        print("No 'Project Tree' section found in the README. No changes made.")
        return

    # Find the end of the "Project Tree" section
    end_index = start_index
    while end_index < len(readme_content) and readme_content[end_index].strip() != "------------":
        end_index += 1

    if end_index >= len(readme_content):
        print("No closing line ('------------') found for 'Project Tree'. No changes made.")
        return

    # Generate the folder tree structure
    tree_structure = generate_tree(root_folder)

    # Replace the old tree structure in the README
    updated_content = (
        readme_content[:start_index] +  # Everything before the tree
        [line + "\n" for line in tree_structure] +  # The new tree structure
        readme_content[end_index:]  # Everything after the closing line
    )

    # Write the updated README.md content
    with open(readme_file, "w", encoding="utf-8") as file:
        file.writelines(updated_content)

    print(f"'Project Tree' section updated in '{readme_file}'.")

def update_file_descriptions(readme_path, json_file="FILE_DESCRIPTIONS.json"):
    """
    Reads the project tree from an existing README.md and updates a FILE_DESCRIPTIONS.json file.

    Parameters:
    - readme_path (str): Path to the README.md file.
    - json_file (str): The name of the JSON file for file descriptions.

    Returns:
    - None
    """

       # Read existing descriptions if the JSON file exists
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            file_descriptions = json.load(f)
    else:
        file_descriptions = {
            "Makefile": "Makefile with commands like `make data` or `make train`",
            "README.md": "The top-level README for developers using this project.",
            "data": "Directory for datasets.",
            "external": "Data from third-party sources.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "docs": "Documentation files.",
            "models": "Trained models and their outputs.",
            "notebooks": "Jupyter or R notebooks for exploratory and explanatory work.",
            "references": "Manuals, data dictionaries, or other resources.",
            "reports": "Generated reports, including figures.",
            "figures": "Generated graphics and figures to be used in reporting.",
            "requirements.txt": "The requirements file for reproducing the analysis environment.",
            "setup.py": "Makes project pip installable (pip install -e .) so `src` can be imported.",
            "src": "Source code for use in this project.",
            "__init__.py": "Makes `src` a Python module.",
            "data": "Scripts to download or generate data.",
            "make_dataset.py": "Script to create datasets.",
            "features": "Scripts to turn raw data into features for modeling.",
            "build_features.py": "Script to build features for modeling.",
            "predict_model.py": "Script to make predictions using trained models."
        }
        # Save to JSON file
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(file_descriptions, file, indent=4, ensure_ascii=False)

    if not os.path.exists(readme_path):
        return 

    # Read the README.md and extract the "Project Tree" section
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Extract the project tree section using regex
    tree_match = re.search(r"Project Tree\s*[-=]+\s*\n([\s\S]+)", readme_content)
    if not tree_match:
        raise ValueError("Project Tree section not found in README.md")

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
            f"| Name             | Location        | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Citation               | License               | Notes                  |\n"
            f"|------------------|-----------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|-----------------------|------------------------|\n"
        )

        full_table = (
            f"| Name             | Files                             | Location        | Provided        | Run Command               | Source           | DOI             | Citation               | License               | Notes                |\n"
            f"|------------------|-----------------------------------|-----------------|-----------------|---------------------------|------------------|-----------------|------------------------|-----------------------|----------------------|\n"
        )

        for entry in data:
            if isinstance(entry, dict):  # Only process dictionary entries
                # Extract required information from the JSON data
                data_name = entry.get("data_name", "N/A")
                data_files = " ; ".join(entry.get("data_files", ["Not available"]))  # Newline separated
                location = entry.get("destination", "N/A")
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
                for file in data_files:
                    full_table += (f"|{data_name}| {file}|{location}|{provided}|{run_command}|{source}|{doi}|{citation}|{license}|{notes}|\n")

                # Format the markdown table for this entry
                markdown_table += (f"|{data_name}| {location}| {provided}|{run_command}|{number_of_files}|{total_size_mb}|{file_formats}|{source}|{doi}|{citation}|{license}|{notes}|\n")
       
        return markdown_table,full_table
    else:
        # If the data is not a list, raise an error
        raise TypeError(f"Expected a list of datasets but got {type(data)}.")

def append_dataset_to_readme(markdown_table, readme_path:str= 'README.md'):
    """
    Appends the generated markdown table to the README file under the 
    'Dataset List' heading.

    Parameters:
        markdown_table (str): The markdown table to be appended.
        readme_path (str): The path to the README file.
    """
    # Read the current content of the README file
    with open(readme_path, 'r') as readme_file:
        content = readme_file.readlines()

    # Check if the 'Data Availability and Provenance Statements' section exists
    heading_found = False
    for i, line in enumerate(content):
        if "Dataset List" in line:
            heading_found = True
            # Insert the markdown table below the heading
            content.insert(i + 1, markdown_table + "\n")
            break
    
    # If the heading is not found, add it at the end
    if not heading_found:
        content.append("\n# Dataset List\n")
        content.append(markdown_table + "\n")

    # Write the updated content back to the README
    with open(readme_path, 'w') as readme_file:
        readme_file.writelines(content)
    print(f"Appended data to {readme_path}")

# CITATION.cff
def create_citation_file(
    project_name,
    version,
    authors,
    orcids,
    code_repo,
    doi=None,
    release_date=None,
):
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
    author_names = authors.split(";") if authors else []
    orcid_list = orcids.split(";") if orcids else []

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
    with open("CITATION.cff", "w") as cff_file:
        yaml.dump(citation_data, cff_file, sort_keys=False)

# Download Readme template:
def download_and_rename_github_file(url:str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md", local_filename:str = "README_template(Social Science Data Editors).md"):
    # Send GET request to the raw file URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content to a file
        with open(local_filename, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download {local_filename} from {url}")
