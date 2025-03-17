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
def creating_readme(repo_name= None, repo_user = None ,project_name=None, project_description= None, code_repo=None, programming_language = None, authors = None, orcids = None, emails = None, activate_cmd = None):

    def create_content(repo_name, repo_user, code_repo,authors, orcids, emails,activate_cmd):
        setup = "```\n"
        if repo_name and repo_user:
            if code_repo.lower() in ["github","gitlab"]:
                web_repo = code_repo.lower()
                setup += f"git clone https://{web_repo}.com/{repo_user}/{repo_name}.git\n"   
        setup += f"cd {repo_name}\n"
        setup += "```\n"

        if activate_cmd:
            setup += f"{activate_cmd}\n"
   
        usage = "```\n"
        usage += "python src/workflow.py\n"
        usage += "```"
        
        contact = ""
        if authors is not None:
            contact += f"- **Name:** {authors}\n"
        if orcids is not None:
            contact += f"- **ORCID:** {orcids}\n"
        if emails is not None:
            contact += f"- **Email:** {emails}\n"
        
        return setup,usage,contact
    
    setup, usage, contact = create_content(repo_name, repo_user, code_repo, authors, orcids, emails, activate_cmd)

     # Create and update README and Project Tree:
    update_file_descriptions("README.md",programming_language, json_file="FILE_DESCRIPTIONS.json")
    generate_readme(project_name, project_description,setup,usage,contact,"README.md")
    create_tree("README.md", ['bin','.git','.datalad','.gitkeep','.env','__pycache__'] ,"FILE_DESCRIPTIONS.json")
    
def generate_readme(project_name, project_description,setup,usage,contact,readme_file = None):
    """
    Generates a README.md file with the project structure (from a tree command),
    project name, and description.

    Parameters:
    - project_name (str): The name of the project.
    - project_description (str): A short description of the project.
    """
    if readme_file is None:
        readme_file = "README.md" 
    if os.path.exists(readme_file):
        return
    

    # Project header
    header = f"""# {project_name}

{project_description}

## Contact Information
{contact}

## Installation
{setup}

## Usage
{usage}

## Project Tree
```

```
"""

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
    def generate_tree(folder_path,file_descriptions,prefix=""):
        """
        Recursively generates a tree structure of the folder.

        Parameters:
        - folder_path (str): The root folder path.
        - prefix (str): The prefix for the current level of the tree.
        """
        tree = []
        items = sorted(os.listdir(folder_path))  # Sort items for consistent structure
        for index, item in enumerate(items):
            if item in ignore_list:
                continue
            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1
            tree_symbol = "└── " if is_last else "├── "
            description = f" <- {file_descriptions.get(item, '')}" if file_descriptions and item in file_descriptions else ""
            tree.append(f"{prefix}{tree_symbol}{item}{description}") # Add spaces for a line break
            if os.path.isdir(item_path):
                child_prefix = f"{prefix}   " if is_last else f"{prefix}│   "
                tree.extend(generate_tree(item_path, prefix=child_prefix))

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
        if "Project Tree" in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "```":
        #if "Project Tree" in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "------------":
            start_index = i + 2 
            break

    if start_index is None:
        print("No 'Project Tree' section found in the README. No changes made.")
        return

    # Find the end of the "Project Tree" section
    end_index = start_index
    while end_index < len(readme_content) and readme_content[end_index].strip() != "```":
    #while end_index < len(readme_content) and readme_content[end_index].strip() != "------------":
        end_index += 1

    if end_index >= len(readme_content):
        print("No closing line ('```') found for 'Project Tree'. No changes made.")
        #print("No closing line ('------------') found for 'Project Tree'. No changes made.")
        return

    # Generate the folder tree structure
    tree_structure = generate_tree(root_folder,file_descriptions)

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

def update_file_descriptions(readme_path,programming_language, json_file="FILE_DESCRIPTIONS.json"):
    """
    Reads the project tree from an existing README.md and updates a FILE_DESCRIPTIONS.json file.

    Parameters:
    - readme_path (str): Path to the README.md file.
    - json_file (str): The name of the JSON file for file descriptions.

    Returns:
    - None
    """

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
        
        # Determine file extension based on programming language
        ext_map = {
            "R": "R",
            "Python": "py",
            "Matlab": "m",
            "Stata": "do",
            "SAS": "sas"
        }

        file_extension = ext_map.get(programming_language, "txt")  # Default to "txt" if language is unknown

        # Generate the descriptions by replacing placeholders in the template
        descriptions = {}
        for key, description in src_template.items():
            file_name = f"{key}.{file_extension}"  # Create the file name with the correct extension
            descriptions[file_name] = description.format(language=programming_language)

        return descriptions

       # Read existing descriptions if the JSON file exists
    
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            file_descriptions = json.load(f)
    else:
        file_descriptions = {
            
            # Directories
            "data": "Directory containing scripts to download or generate data.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "src": "Directory containing source code for use in this project.",
            "docs": "Directory for documentation files.",
            "notebooks": "Directory for Jupyter or R notebooks for exploratory and explanatory work.",
            "results": "Directory for generated results from the project.",
            "setup": "Directory containing setup files and scripts to configure the project environment.",

            # Setup files
            ".cookiecutter": "Cookiecutter template configuration for creating new project structures.",
            ".gitignore": "Specifies files and directories that should be ignored by Git.",
            "CITATION.cff": "File containing citation information for the project, typically used for academic purposes.",
            "FILE_DESCRIPTIONS.json": "JSON file containing descriptions of the project files for reference.",
            "LICENSE.txt": "The project's license file, outlining terms and conditions for usage and distribution.",
            "README.md": "The top-level README for developers using this project.",
            "requirements.txt": "The requirements file for reproducing the analysis environment.",
       
             # Setup files
            "deic_storage_download.py": "Script to download data from DEIC storage for the project.",
            "dependencies.txt": "List of external dependencies required for the project, typically installed with pip.",
            "get_dependencies.py": "Checks and retrieves necessary dependencies for the project setup.",
            "install_dependencies.py": "Installs any missing dependencies listed in `dependencies.txt` or other sources.",
            "readme_templates.py": "Script that provides templates for README files for different setups or environments.",
            "set_raw_data.py": "Script to set up raw data for use in the project, including preprocessing steps.",
            "setup.ps1": "PowerShell script for setting up the environment, configuring necessary settings.",
            "setup.py": "Makes project pip installable (pip install -e .) so `src` can be imported.",
            "setup.sh": "Bash script for setting up the environment, configuring necessary settings.",
            "update_requirements.py": "Script to update the `requirements.txt` file with the latest dependencies.",
            "utils.py": "Contains utility functions for common tasks throughout the setup process."
            
        }


        if programming_language:
            # Update the existing dictionary with the new descriptions
            file_descriptions.update(src_file_descriptions(programming_language))

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
        print("Project Tree section not found in README.md")
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
    with open("CITATION.cff", "w") as cff_file:
        yaml.dump(citation_data, cff_file, sort_keys=False)

# Download Readme template:
def download_README_template(url:str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md", local_file:str = "README_template(Social Science Data Editors).md"):
    
     # Check if the local file already exists
    if os.path.exists(local_file):
        return
    
    # Ensure the parent directory exists
    folder_path = os.path.dirname(local_file)
    os.makedirs(folder_path, exist_ok=True)

    # Send GET request to the raw file URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content to a file
        with open(local_file, 'wb') as file:
            file.write(response.content)
    else:
        print(f"Failed to download {local_file} from {url}")
