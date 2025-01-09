import os
import pathlib
import platform  # Add platform module

# Change to project root directory
project_root = pathlib.Path(__file__).resolve().parent.parent
os.chdir(project_root)

def update_requirements(dependencies_files: list = ["src/dependencies.txt"], 
                                 readme_file: str = "README.md", 
                                 sections: list = ["src"]):
    # Ensure the lengths of dependencies_files and sections match
    if len(dependencies_files) != len(sections):
        raise ValueError("The number of dependencies files must match the number of sections.")

    # Initialize the Software Requirements section with the header
    software_requirements_section = "### Software Requirements\n\n"
    software_requirements_section += f"**The software below were installed on the follow operation system: {platform.platform() }**\n\n"

    # Iterate through all dependency files and corresponding sections
    for idx, (dependencies_file, section) in enumerate(zip(dependencies_files, sections)):
        # Check if the dependencies file exists
        if not os.path.exists(dependencies_file):
            print(f"Dependencies file '{dependencies_file}' not found. Skipping.")
            continue

        # Read the content from the dependencies file
        with open(dependencies_file, "r") as f:
            content = f.readlines()

        current_software = None
        software_dependencies = {}

        # Parse the dependencies file
        for i, line in enumerate(content):
            line = line.strip()

            if line == "Software version:" and i + 1 < len(content):
                current_software = content[i + 1].strip()
                software_dependencies[current_software] = {"install_cmd": None, "dependencies": []}
                continue

            if line == "Install Command:" and current_software:
                install_cmd = content[i + 1].strip()
                software_dependencies[current_software]["install_cmd"] = install_cmd

                if "pip" in install_cmd:
                    install_str = f"**To replicate the environment below, please run '{install_cmd}' within {current_software} as the initial step. See [this guide](https://pip.pypa.io/en/stable/user_guide/#ensuring-repeatability) for further info on using the 'requirements.txt'.**\n"
                elif "conda" in install_cmd:
                    install_str = f"**To replicate the {current_software} environment below (using Conda), please run '{install_cmd}'as the initial step. For further info Conda environments, visit [this page](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).**\n"
                else:
                    install_str = f"**To install the dependencies below, please run '{install_cmd}' within {current_software} as the first step to replicate the environment.**\n\n"

                software_dependencies[current_software]["install_cmd"] = install_str
                continue

            if line == "Dependencies:":
                continue

            if current_software and "==" in line:
                package, version = line.split("==")
                software_dependencies[current_software]["dependencies"].append((package, version))

        # Add the subheading section if it exists
        if section:
            software_requirements_section += f"\n#### **{section}**\n"
        
        # Correctly loop through the dictionary
        for software, details in software_dependencies.items():
            install_cmd = details["install_cmd"]
            dependencies = details["dependencies"]
            software_requirements_section += install_cmd
            software_requirements_section += f"\n**{software}**\n"
            for package, version in dependencies:
                software_requirements_section += f"  - {package}: {version}\n"

        software_requirements_section += "\n---\n"

    # Check if the README file exists
    try:
        with open(readme_file, "r") as f:
            readme_content = f.read()

        # Check if the "### Software Requirements" section exists
        if "### Software Requirements" in readme_content:
            # Find the "### Software Requirements" section and replace it
            start = readme_content.find("### Software Requirements")
            end = readme_content.find("\n## ", start + 1)
            if end == -1:
                end = len(readme_content)  # No further sections, overwrite until the end
            updated_content = readme_content[:start] + software_requirements_section.strip() + readme_content[end:]
        else:
            # Append the new section at the end
            updated_content = readme_content.strip() + "\n\n" + software_requirements_section.strip()
    except FileNotFoundError:
        # If the README file doesn't exist, create it with the new section
        updated_content = software_requirements_section.strip()

    updated_content = updated_content.replace("---## Software Requirements","")

    # Write the updated content to the README file
    with open(readme_file, "w") as f:
        f.write(updated_content.strip())

    print(f"{readme_file} successfully updated.")

if __name__ == "__main__":
    update_requirements(dependencies_files=["src/dependencies.txt", "setup/dependencies.txt"], 
                                 sections=["src", "setup"])
