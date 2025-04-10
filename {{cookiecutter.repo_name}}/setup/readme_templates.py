import os
import subprocess
import sys
import json
import re
import os
import json
import subprocess
import sys

from utils import *

pip_installer(required_libraries =  ['python-dotenv','pyyaml','requests'])

from dotenv import dotenv_values, load_dotenv
import yaml
import requests

# Determine file extension based on programming language
ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}

       # file_extension = ext_map.get(programming_language, "txt")  # Default to "txt" if language is unknown

# README.md
def creating_readme(repo_name= None, repo_user = None ,project_name=None, project_description= None, code_repo=None, programming_language = "None", authors = None, orcids = None, emails = None, activate_cmd = None):

    def create_content(repo_name, repo_user, code_repo,authors, orcids, emails,activate_cmd,programming_language):
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
        if programming_language.lower() != "none":
            file_extension = ext_map.get(programming_language.lower(), "txt")
            usage += f"{programming_language.lower()} src/main.{file_extension}\n"
        
        usage += "```"
            
        contact = ""
        if authors:
            contact += f"- **Name:** {authors}\n"
        if orcids:
            contact += f"- **ORCID:** {orcids}\n"
        if emails:
            contact += f"- **Email:** {emails}\n"
        
        return setup,usage,contact
    
    setup, usage, contact = create_content(repo_name, repo_user, code_repo, authors, orcids, emails, activate_cmd,programming_language)

    file_description = pathlib.Path(__file__).resolve().parent.parent / pathlib.Path("./setup/FILE_DESCRIPTIONS.json")
     # Create and update README and Project Tree:
    update_file_descriptions("./README.md",programming_language, json_file=file_description)
    generate_readme(project_name, project_description,setup,usage,contact,"./README.md")
    create_tree("./README.md", ["bin",".git",".datalad",".gitkeep",".env","__pycache__"] ,file_description)
    
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


    readme_file= pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(readme_file)

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
The current repository structure is shown in the tree below, and descriptions for each file can be found or edited in the FILE_DESCRIPTIONS.json file.
```

```

## Creating a Replication Package Based on DCAS

To create a replication package that adheres to the [DCAS (Data and Code Sharing) standard](https://datacodestandard.org/), follow the guidelines ([AEA Data Editor's guidance](https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html)) provided by the Social Science Data Editors. This ensures your research code and data are shared in a clear, reproducible format.

The following are examples of journals that endorse the Data and Code Availability Standard:

- [American Economic Journal: Applied Economics](https://www.aeaweb.org/journals/applied-economics)
- [Econometrica](https://www.econometricsociety.org/publications/econometrica)
- [Economic Inquiry](https://onlinelibrary.wiley.com/journal/14680299)
- [Journal of Economic Perspectives](https://www.aeaweb.org/journals/jep)

For a full list of journals, visit [here](https://datacodestandard.org/journals/).

Individual journal policies may differ slightly. To ensure full compliance, check the policies and submission guidelines of the journal.


## Dataset List

## Computational Requirements

### Software Requirements
    
"""

    # Write the README.md content
    with open(readme_file, "w",encoding="utf-8") as file:
        file.write(header)
    print(f"README.md created at: {readme_file}")

# Project Tree
def create_tree(readme_file=None, ignore_list=None, json_file="./setup/FILE_DESCRIPTIONS.json", root_folder=None):
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
                tree.extend(generate_tree(item_path,file_descriptions, prefix=child_prefix))

        return tree

    json_file = pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(json_file)

    if not readme_file:
        readme_file = "README.md"
    
    readme_file= pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(readme_file)

    if not os.path.exists(readme_file):
        print(f"README file '{readme_file}' does not exist. Exiting.")
        return

    if ignore_list is None:
        ignore_list = []  # Default to an empty list if not provided


    if isinstance(json_file, str) and json_file.endswith(".json") and os.path.exists(json_file): 
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
        #if "Project Tree" in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "```":
        if "The current repository structure is shown in the tree below, and descriptions for each file can be found or edited in the FILE_DESCRIPTIONS.json file." in line.strip() and i + 1 < len(readme_content) and readme_content[i + 1].strip() == "```":
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

def update_file_descriptions(readme_file,programming_language, json_file="./setup/FILE_DESCRIPTIONS.json"):
    """
    Reads the project tree from an existing README.md and updates a FILE_DESCRIPTIONS.json file.

    Parameters:
    - readme_file (str): Path to the README.md file.
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
        

        file_extension = ext_map.get(programming_language.lower(), "txt")  # Default to "txt" if language is unknown

        # Generate the descriptions by replacing placeholders in the template
        descriptions = {}
        for key, description in src_template.items():
            file_name = f"{key}.{file_extension}"  # Create the file name with the correct extension
            descriptions[file_name] = description.format(language=programming_language)

        return descriptions

       # Read existing descriptions if the JSON file exists
    

    json_file = pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(json_file)

    if not readme_file:
        readme_file = "README.md"
    
    readme_file= pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(readme_file)

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            file_descriptions = json.load(f)
    else:
        file_descriptions = {
            
            # Directories
            "data": "Directory containing scripts to download or generate data.",
            "external":"Data from third party sources.",
            "interim": "Intermediate data transformed during the workflow.",
            "processed": "The final, clean data used for analysis or modeling.",
            "raw": "Original, immutable raw data.",
            "src": "Directory containing source code for use in this project.",
            "docs": "Directory for documentation files.",
            "notebooks": "Directory for Jupyter or R notebooks for exploratory and explanatory work.",
            "results": "Directory for generated results from the project.",
            "setup": "Directory containing setup files and scripts to configure the project environment.",
            "DCAS template": "Directory containing 'replication package' template for the DCAS (Data and Code Sharing) standard",

            # Setup files
            ".cookiecutter": "Cookiecutter template configuration for creating new project structures.",
            ".gitignore": "Specifies files and directories that should be ignored by Git.",
            "CITATION.cff": "File containing citation information for the project, typically used for academic purposes.",
            "FILE_DESCRIPTIONS.json": "JSON file containing descriptions of the project files for reference.",
            "LICENSE.txt": "The project's license file, outlining terms and conditions for usage and distribution.",
            "README.md": "The top-level README for developers using this project.",
            "README.MD": "Current The top-level README for developers using this project.",
            "README_DCAS.md": "A template README for social science replication packages: https://social-science-data-editors.github.io/template_README/",
            "requirements.txt": "The requirements file for reproducing the analysis environment.",
            ".gitlog": "git log file (created using git log --all --pretty=fuller --stat > data.txt) tracking changes to the git repository",
       
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

    if not os.path.exists(readme_file):
        return 

    # Read the README.md and extract the "Project Tree" section
    with open(readme_file, "r", encoding="utf-8") as f:
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
                data_sizes = " ; ".join(entry.get("data_size", ["Not available"]))  # Newline separated
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
    section_title = "## Dataset List"
    new_dataset_section = f"{section_title}\n\n{markdown_table.strip()}\n"


    if not readme_file:
        readme_file = "README.md"
    
    readme_file= pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(readme_file)

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
    with open("CITATION.cff", "w") as cff_file:
        yaml.dump(citation_data, cff_file, sort_keys=False)

# Download Readme template:
def download_README_template(url:str = "https://raw.githubusercontent.com/social-science-data-editors/template_README/release-candidate/templates/README.md", readme_file:str = "./README_DCAS_template.md"):
    
    readme_file= pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(readme_file)

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
