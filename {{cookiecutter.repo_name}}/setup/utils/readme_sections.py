import os
import re
import platform
from datetime import datetime
import pathlib
import fnmatch

from .general_tools import *
from .toml_tools import *


package_installer(required_libraries =  ['psutil',"py-cpuinfo"])

import psutil
import cpuinfo


extension_map = {
        "r": (".R", ".Rmd"),
        "python": (".py", ".ipynb"),
        "stata": (".do", ".ipynb"),
        "matlab": (".m", [".ipynb", ".mlx"]),
        "sas": (".sas", ".ipynb")
}

def main_text(json_file, code_path):
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter")
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = load_from_env("CODE_REPO", ".cookiecutter")
    authors = load_from_env("AUTHORS", ".cookiecutter")
    orcids = load_from_env("ORCIDS", ".cookiecutter")
    emails = load_from_env("EMAIL", ".cookiecutter")
    project_name = load_from_env("PROJECT_NAME", ".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION", ".cookiecutter")
    py_manager = load_from_env("PYTHON_ENV_MANAGER", ".cookiecutter")

    # Determine repo host and user
    if code_repo.lower() == "github":
        repo_user = load_from_env("GITHUB_USER")
        hostname = load_from_env("GITHUB_HOSTNAME") or "github.com"
    elif code_repo.lower() == "gitlab":
        repo_user = load_from_env("GITLAB_USER")
        hostname = load_from_env("GITLAB_HOSTNAME") or "gitlab.com"
    elif code_repo.lower() == "codeberg":
        repo_user = load_from_env("CODEBERG_USER")
        hostname = load_from_env("CODEBERG_HOSTNAME") or "codeberg.org"
    else:
        repo_user, hostname = None, None

    py_version = get_version("python")
    software_version = get_version(programming_language)
    conda_version = get_version("conda") if py_manager.lower() == "conda" else "conda"
    pip_version = get_version("pip")
    uv_version = get_version("uv")

    install = set_setup(programming_language, py_version, software_version, conda_version, pip_version, uv_version, repo_name, repo_user, hostname)
    activate = set_activate()
    contact = set_contact(authors, orcids, emails)
    usage, run_command = set_scripts(programming_language, code_path, json_file)
    config = set_config_table(programming_language)
    cli_tools = set_cli_tools(programming_language)
    dcas = set_dcas()
    code_path = language_dirs.get(programming_language.lower())


    system_spec = set_specs()
    ci_tools = set_ci_tools(programming_language, code_repo)
    unit_tests = set_unit_tests(programming_language)


    dataset = set_dataset()

    if programming_language.lower() != "python":
        head = f"📋 Instructions for installing {py_version}, {software_version}, and dependencies"
    else:
        head = f"📋 Instructions for installing {software_version}, and dependencies"
    header = f"""# {project_name}

{project_description}

## 👤 Author & Contact

{contact}

<details>
<summary><strong>🖥️ System Specifications </strong></summary><br>

{system_spec}

</details>

<details>
<summary><strong>🔧 Initial Setup</strong></summary><br>

{head}

{install}

</details>

<details>
<summary><strong>⚡Project Activation</strong></summary><br>

To configure the project's environment—including project paths, environment variables, and virtual environments—run the activation script for your operating system. These scripts read settings from the `.env` file.

{activate}

</details>

<details>
<summary><strong>📜 Code Scripts</strong></summary><br>

The project is written in **{software_version}** and includes modular scripts for standardized workflows, organized under `{code_path}`.

##### ▶️ Run the Main Script

To execute the full workflow pipeline, run the main orchestration script from the terminal:

```
{run_command}
```

<details>
<summary><strong>Expand for showing detected Scripts:</strong></summary>

{usage}

</details>
</details>

<details>
<summary><strong>🧪 Unit Testing</strong></summary><br>

{unit_tests}

</details>

<details>
<summary><strong>⚙️ Continuous Integration (CI)</strong></summary><br>

{ci_tools}

</details>

<details>
<summary><strong>🗂️ Configuration Files (Root-Level)</strong></summary><br>

{config}

</details>

<details>
<summary><strong>🧰 CLI Utilities</strong></summary><br>

{cli_tools}

</details>

<details>
<summary><strong>📦 Dataset List</strong></summary><br>

{dataset}

</details>

<details>
<summary><strong>📁 Project Directory Structure</strong></summary><br>

The current repository structure is shown below. Descriptions can be edited in `./pyproject.toml`.

```tree

```

</details>
"""
    return header

def set_activate():

    os_type = platform.system().lower()
    if os_type == "windows":

        usage =f"""**On Windows (PowerShell)**
        
        ```powershell
        # Activate
        ./activate.ps1
        
        # Deactivate
        ./deactivate.ps1
        ```"""
    elif os_type in ("darwin", "linux"):

        usage =f"""**On Linux/macOS (bash)**
        
        ```bash
        # Activate
        source activate.sh
        
        # Deactivate
        source deactivate.sh
        ```"""
           
    return usage

def set_setup(programming_language,py_version,software_version,conda_version,pip_version,uv_version,repo_name, repo_user,hostname):            
    
    
    code_path = language_dirs.get(programming_language.lower())

    #setup_dependencies = read_dependencies(str(pathlib.Path(__file__).resolve().parent.parent.parent / "setup/dependencies.txt"))
    code_dependencies = read_dependencies(str(pathlib.Path(__file__).resolve().parent.parent.parent / f"{code_path}/dependencies.txt"))
    
    setup = ""

    if repo_name and repo_user:
        setup += "#### Clone the Project Repository\n"
        "This will donwload the repository to your local machine. '.env' file is not include in the online repository.\n"
        "Clone the repository using the following command:\n"
        setup += "```\n"
        if hostname:
            setup += (f"git clone https://{hostname}/{repo_user}/{repo_name}.git\n"   
                    "```\n")
    setup += ("#### Navigate to the Project Directory\n"
            "Change into the project directory:\n"  
            "```\n"
            f"cd {repo_name}\n"
            "```\n")

    setup += f"#### {py_version}\n"
    
    if programming_language.lower() == "python":
        setup += f"Project environment using {software_version} can be setup using the options described below.\n\n"
    else:
        setup += f"Project `./setup` environment using **{py_version}** ccan be setup using the options described below.\n\n"
  
    setup += f">Only the **Conda** will install **{py_version}** along with its dependencies. For pip and uv installation methods, **{py_version}** must already be installed on your system.\n\n"

    if programming_language.lower() in ["matlab","stata","sas"]:
        f"Project `code` environment using **{software_version}** can be installed using the options described below.\n\n"

        setup +=f"These methods do **not** install external the proprietary software **{software_version}** which to be installed manually.\n\n"


    setup +=f"""<details>
<summary><strong>Uv Installation (Recommended)</strong></summary><br>

If you prefer a faster and more reproducible alternative to pip, you can use **[{uv_version}](https://github.com/astral-sh/uv)** with **{py_version}** to install the dependencies.

To install using `requirements.txt`:

```
uv pip install -r requirements.txt
```

Or, if a `uv.lock` file is available and you want full reproducibility:

```
uv pip install --strict uv.lock
```

</details>

"""
    
    setup +=f"""<details>
<summary><strong>Pip Installation:</strong></summary><br>

You can install the Python dependencies using **{py_version}** and **{pip_version}** and the provided`requirements.txt`::

```
pip install -r requirements.txt
```
</details>

"""
    
    if programming_language.lower() == "r":
        conda_title = f"Conda Installation (Installs **{py_version}** and **{software_version}**)"
    else:
        conda_title = f"Conda Installation (Installs **{py_version}**)"


    setup +=f"""<details>
<summary><strong>{conda_title}</strong></summary><br>

Install the required dependencies using **{conda_version}** and the provided `environment.yml` file:

```
conda env create -f environment.yml
```
</details>

"""
    setup +=f"""#### Installing the `setup` package

Once you have installed the python environmnet Conda, Pip or Uv, you must also install the local `setup` package used for configuration and automation scripts:

```
cd setup
pip install -e .
cd ..
```

This makes CLI tools such as `run-setup`, `update-readme`, and `set-dataset` available in your environment.

"""
    if programming_language.lower() == "python":
        setup +=f"""#### {software_version}

The project code in `{code_path}` is written in **{software_version}** with the detected {software_version} dependencies are listed below:

```code_dependencies 
{code_dependencies}
```
"""
    if programming_language.lower() == "r":

        setup +=f"""#### {software_version}

The project code in `{code_path}` is written in **{software_version}** and can be set up using one of the option described below.

To use **{software_version}**, it must already be installed on your system.

>**Conda** is the only installation method described earlier that will install **{software_version}** automatically.

The detected {software_version} dependencies are listed below:

```code_dependencies 
{code_dependencies}
```

##### Renv Installation

To install R packages required by this project, use the `renv` package within the `/R` directory and the provided lock file (`renv.lock`):

```
cd R
Rscript -e \"renv::restore()\"
```
> ⚠️ Warning: Ensure you are using **{software_version}** for full compatibility. If `renv` is not already installed, run:

```
install.packages("renv")
```

"""    
    if programming_language.lower() in ["matlab","stata"]:

        setup += f"""#### {software_version}

The project code in `{code_path}` is written in **{software_version}** and requires it to be pre-installed on your system. Once {software_version} is available, you can set up the environment using one of the options described below.

The following dependencies have been detected for **{software_version}**:

```code_dependencies 
{code_dependencies}
```
"""

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

def find_scripts(folder_path, source_ext, notebook_ext):
    if isinstance(notebook_ext, str):
        notebook_exts = [notebook_ext.lower()]
    else:
        notebook_exts = [ext.lower() for ext in notebook_ext]

    #prefix_pattern = re.compile(r'^s(\d{2})_', re.IGNORECASE)
    found = []

    for root, _, files in os.walk(folder_path):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext == source_ext.lower():
                kind = "source"
            elif ext in notebook_exts:
                kind = "notebook"
            else:
                continue

            #m = prefix_pattern.match(fn)
            #if not m:
            #    continue
            #prefix = int(m.group(1))
            found.append((kind, os.path.join(root, fn)))

    #found.sort(key=lambda x: x[0])
    #return [(kind, path) for _, kind, path in found]
    return found

def get_run_command(orchestrator, programming_language):
    if not orchestrator:
        return None

    script_name = os.path.relpath(orchestrator).replace("\\", "/")
    base_name = os.path.splitext(os.path.basename(script_name))[0]

    command_map = {
        "python": lambda s: f"python {s}",
        "r": lambda s: f"Rscript {s}",
        "stata": lambda s: f"stata-mp -b do {s}",
        "matlab": lambda s: f'matlab -batch "{base_name}"',
        "sas": lambda s: f"sas {s}",
    }

    return command_map.get(programming_language.lower(), lambda s: f"<run {s}>")(script_name)

def set_scripts(programming_language,folder_path, json_file="./file_description.json"):
    """
    Generate the README section for Script Structure and Usage based on the programming language,
    and return the appropriate run command for the main orchestration script.

    Returns:
        tuple[str, str]: (Formatted markdown for README, run command string)
    """

    programming_language = programming_language.lower()
    if programming_language not in ["r", "python", "stata", "matlab", "sas"]:
        raise ValueError("Supported programming languages are: r, python, stata, matlab, sas.")

    # Set extensions
    source_ext, notebook_ext = extension_map.get(programming_language.lower(), (".txt", ".txt"))

    scripts = find_scripts(folder_path, source_ext, notebook_ext)

    # Dectect Scripts
    file_descriptions = read_toml_json(json_filename=json_file, tool_name="file_descriptions", toml_path="pyproject.toml")
    if not file_descriptions:
        file_descriptions = {}
    md = []
    for _, path in scripts:
        name = os.path.basename(path)
        display = os.path.splitext(name)[0].replace("_", " ").title()
        desc = file_descriptions.get(name)
        if desc:
            md.append(f"- **{display}** (`{name}`) — {desc}")
        else:
            md.append(f"- **{display}** (`{name}`)")

    md.append("")

    if any("utils" in os.path.basename(p).lower() for _, p in scripts):
        md.append("🛠️ **Note**: `utils` does not define a `main()` function and should not be executed directly.\n")

    orch_candidates = [path for kind, path in scripts if kind == "source" and os.path.basename(path).lower().startswith("s00_")] or \
                  [path for kind, path in scripts if kind == "source" and os.path.basename(path).lower().startswith("main")]

    orchestrator = orch_candidates[0] if orch_candidates else None

    if orchestrator:
        md.append(f"**The Content of the orchestration script `{os.path.basename(orchestrator)}` shown below:**\n")
        try:
            code = open(orchestrator, encoding="utf-8").read().rstrip()
            md.append(f"```{programming_language.lower()}\n{code}\n```")
        except Exception as e:
            md.append(f"_Failed to read orchestrator script: {e}_")

    # Determine run command for README
    run_command = get_run_command(orchestrator, programming_language)

    return "\n".join(md), run_command

def set_config_table(programming_language, project_root="."):
    base_config = """The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.

| File              | Purpose                                                                                          |
|-------------------|--------------------------------------------------------------------------------------------------|
| `pyproject.toml`  | Project metadata for packaging, CLI tools, sync rules, platform logic, and documentation         |
| `.env`            | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `.gitignore`      | Excludes unnecessary files from Git version control                                              |
| `environment.yml` | Conda environment definition for Python/R, including packages and versions                       |
| `requirements.txt`| Pip-based Python dependencies for lightweight environments                                       |
"""

    if programming_language.lower() == "r":
        base_config += "| `renv.lock`         | Records the exact versions of R packages used in the project                                   |\n"

    uv_lock_path = os.path.join(project_root, "uv.lock")
    if os.path.exists(uv_lock_path):
        base_config += "| `uv.lock`           | Locked Python dependencies file for reproducible installs with `uv`                            |\n"

    # Add pyproject.toml section explanation
    base_config += """

---

#### 📄 `pyproject.toml` Sections Explained

| Section                   | Purpose                                                                                      |
|---------------------------|----------------------------------------------------------------------------------------------|
| `[project]`               | Declares the base project metadata for Python tooling (name, version, dependencies, etc.).   |
| `[tool.uv]`               | Placeholder for settings related to the uv package manager (currently unused).               |
| `[tool.cookiecutter]`     | Stores project template metadata (e.g., author, licenses, language) for reproducibility and scaffolding. |
| `[tool.rcloneignore]`     | Defines file patterns to ignore when syncing with remote tools like Rclone.                  |
| `[tool.treeignore]`       | Specifies which files and folders to exclude from directory tree visualizations.             |
| `[tool.platform_rules]`   | Maps Python packages to operating systems for conditional installations.                     |
| `[tool.file_descriptions]`| Contains descriptions of files and directories for automation, UI labels, and documentation. |
"""

    return base_config

def set_cli_tools(programming_language):

    code_path = language_dirs.get(programming_language.lower())

    cli_tools = f"""
The `setup` Python package provides a collection of command-line utilities to support project configuration, dependency management, documentation, and reproducibility workflows.

ℹ️ **Note**: To use these commands, you must first install the local `setup` package.  

Refer to the [Installation](#installation) section for details on how to install it using `pip install -e .` from the `setup/` directory.

After installing the setup package, the following commands become available from the terminal:


| Command                  | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| `push-backup`             | Executes a full project backup using preconfigured rules and paths.                         |
| `set-dataset`            | Initializes or registers datasets for use in the project (e.g., adds metadata or links).    |
| `update-dependencies`    | Retrieves current dependencies required by the project `./setup` and `{code_path}`.               |
| `run-setup` (in progress)| Main entry point to initialize or reconfigure the project environment.                      |
| `update-readme`          | Automatically updates the main `README.md` file with current metadata and structure.        |
| `reset-templates`        | Resets or regenerates the code templates for `{code_path}`.                                       |
| `code-examples`          | Generates example code and notebooks for supported languages (Python, R, SAS, etc.).        |
| `dcas-migrate`(in progress)| Migrates and validates the project structure for DCAS (Data and Code Availability Standard) compliance.|


After activating your environment, run commands like:

```
run-setup
set-dataset
update-requirements
```
"""
    return cli_tools

def set_unit_tests(programming_language: str) -> str:

    lang_info = {
        "python": {
            "test_framework": "`pytest`",
            "code_folder": "`src/`",
            "test_folder": "`tests/`",
            "test_format": "`test_*.py`",
            "package_file": "`requirements.txt`",
            "example": """**Example layout:**

```
src/s00_main.py
tests/test_s00_main.py
```

**Run tests:**

```
pytest
```
"""
        },
        "r": {
            "test_framework": "`testthat`",
            "code_folder": "`R/`",
            "test_folder": "`tests/testthat/`",
            "test_format": "`test-*.R`",
            "package_file": "`renv.lock`",
            "example": """**Example layout:**

```
R/s00_main.R
tests/testthat/test-s00_main.R
```

**Run tests:**

```
testthat::test_dir("tests/testthat")
```

**From command line:**

```
Rscript -e 'testthat::test_dir("tests/testthat")'
```
"""
        },
        "matlab": {
            "test_framework": "`matlab.unittest`",
            "code_folder": "`src/`",
            "test_folder": "`tests/`",
            "test_format": "`test_*.m`",
            "package_file": "",
            "example": """**Example layout:**

```
src/s00_main.m
tests/test_s00_main.m
```

**Run tests in MATLAB:**

```
results = runtests('tests');
assert(all([results.Passed]), 'Some tests failed')
```

**From command line:**

```
matlab -batch "results = runtests('tests'); assert(all([results.Passed]), 'Some tests failed')"
```
"""
        },
        "stata": {
            "test_framework": "`.do` script-based",
            "code_folder": "`stata/do/`",
            "test_folder": "`tests/`",
            "test_format": "`test_*.do`",
            "package_file": "",
            "example": """**Example layout:**

```
stata/do/s00_main.do
tests/test_s00_main.do
```

**Run tests in Stata:**

```
do tests/test_s00_main.do
```

**From command line:**

```
stata -b do tests/test_s00_main.do
```
"""
        }
    }

    if programming_language.lower() not in lang_info:
        return f"Unsupported language: {programming_language}"

    lang = lang_info[programming_language.lower()]
    
    folder_path = pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(lang["test_folder"].replace("`", ""))
    md = f"""

This template includes built-in support for **unit testing** in {programming_language.capitalize()} to promote research reliability and reproducibility.

| Language | Test Framework     | Code Folder | Test Folder       | Test File Format |
| -------- | ------------------ | ----------- | ----------------- | ---------------- |
| {programming_language.capitalize()}   | {lang['test_framework']} | {lang['code_folder']} | {lang['test_folder']} | {lang['test_format']} |


{lang['example']}

""".strip()

    if not folder_path.exists():
        md += f"⚠️ Test folder not found: `{lang['test_folder']}`"
    else:
        # Filter test scripts based on naming convention
        test_pattern = lang["test_format"].replace("`", "")
        test_scripts = [file for file in os.listdir(str(folder_path)) if fnmatch.fnmatch(file, test_pattern)]

        if not test_scripts:
            md +=f"\n\n⚠️ No valid test scripts were detected in `{lang['test_folder']}`.\nMake sure test files follow the expected format: `{lang['test_format']}`"
        else:
            md +=f"\n\nThe following test scripts were detected in `{lang['test_folder']}`:\n"
            for name in test_scripts:
                md +=f"- **{name}**\n"

    return md

def set_ci_tools(programming_language: str, code_repo: str) -> str:
    
    ci_matrix = {
        "github": {
            "supports": ["python", "r", "matlab"],
            "config_file": ".github/workflows/ci.yml",
            "note": ""
        },
        "gitlab": {
            "supports": ["python", "r", "matlab"],
            "config_file": ".gitlab-ci.yml",
            "note": ""
        },
        "codeberg": {
            "supports": ["python", "r"],
            "config_file": ".woodpecker.yml",
            "note": """⚠️ No support for MATLAB or cross-platform testing.  
📝 CI is not enabled by default – to activate CI for your repository, you must [submit a request](https://codeberg.org/Codeberg-e.V./requests/issues/new?template=ISSUE_TEMPLATE%2fWoodpecker-CI.yaml).  
More information: [Codeberg CI docs](https://docs.codeberg.org/ci/)"""
        }
    }

    lang_info = {
        "python": {"package_file": "`requirements.txt`"},
        "r": {"package_file": "`renv.lock`"},
        "matlab": {"package_file": ""},
        "stata": {"package_file": ""}
    }

    if programming_language.lower() not in lang_info:
        return f"Unsupported language: {programming_language}"
    if code_repo.lower() not in ci_matrix:
        return f"Unsupported code repository: {code_repo}"
    if programming_language.lower() not in ci_matrix[code_repo.lower()]["supports"]:
        return f"{programming_language.capitalize()} is not supported on {code_repo.capitalize()}."

    lang = lang_info[programming_language.lower()]
    ci = ci_matrix[code_repo.lower()]

    if lang["package_file"]:
        pipeline = f"""##### Each pipeline:
1. Installs language runtime and dependencies  
2. Installs project packages using {lang['package_file']}  
3. Runs tests in `tests/`  
4. Outputs results and logs"""
    else:
        pipeline = f"""##### Each pipeline:
1. Installs language runtime and dependencies  
2. Runs tests in `tests/`  
3. Outputs results and logs"""

    config_file = pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(ci['config_file'])

    md = f"""

CI is configured for **{code_repo.capitalize()}** (`{ci['config_file']}`) with **{programming_language.capitalize()}** support.

✅ Even without writing **unit tests**, the default CI configuration will still verify that your project environment installs correctly across platforms (e.g., Linux, Windows, macOS). This provides early detection of broken dependencies, incompatible packages, or missing setup steps — critical for collaboration and long-term reproducibility.

##### 🔄 CI Control via CLI

CI can be toggled on or off using the built-in CLI command:

```
ci-control --on
ci-control --off 
```

{pipeline}

{ci['note']}


##### 🧷 Git Shortcut for Skipping CI

To skip CI on a commit, use the built-in Git alias:

```
git commit-skip "Updated documentation"
```
""".strip()

    return md

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

def set_dataset():

    return f""" To set up or configure a dataset, run the following command:

```
set-dataset
```

**The following datasets are included in the project:**

| Name             | Location        |Hash                       | Provided        | Run Command               | Number of Files | Total Size (MB) | File Formats         | Source          | DOI                | Citation               | License               | Notes                  |
|------------------|-----------------|---------------------------|-----------------|---------------------------|-----------------|-----------------|----------------------|-----------------|--------------------|------------------------|-----------------------|------------------------|
"""

def read_dependencies(dependencies_file):
    
    def collect_dependencies(content):
        
        current_software = None
        software_dependencies = {}

        # Parse the dependencies file
        for i, line in enumerate(content):
            line = line.strip()

            if line == "Software version:" and i + 1 < len(content):
                current_software = content[i + 1].strip()
                software_dependencies[current_software] = {"dependencies": []}
                continue

            if line == "Dependencies:":
                continue
            
            if current_software and "==" in line:
                package, version = line.split("==")
                software_dependencies[current_software]["dependencies"].append((package, version))
        
        return software_dependencies, package, version

    software_requirements_section = ""

    # Check if the dependencies file exists
    if not os.path.exists(dependencies_file):
        return software_requirements_section

    # Read the content from the dependencies file
    with open(dependencies_file, "r") as f:
        content = f.readlines()

    software_dependencies, package, version = collect_dependencies(content)

    # Correctly loop through the dictionary
    for software, details in software_dependencies.items():
            
        for package, version in details["dependencies"]:
            software_requirements_section += f"{package}: {version}\n"

    software_requirements_section += "\n\n"

    return software_requirements_section

def set_specs():

    system_spec = get_system_specs()

    specs = f"""
    
The project was developed and tested on the following operating system:

{system_spec}

"""
    return specs 

def get_system_specs():
    
    def detect_gpu():
        # Try NVIDIA
        if shutil.which("nvidia-smi"):
            try:
                output = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                gpus = output.splitlines()
                return ", ".join(gpus) if gpus else None
            except Exception:
                return None

        # Try PyTorch
        try:
            import torch
            if torch.cuda.is_available():
                gpus = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
                return ", ".join(gpus)
        except ImportError:
            pass

        # Try AMD (Linux)
        if platform.system() == "Linux":
            try:
                lspci_output = subprocess.check_output(["lspci"], text=True)
                amd_gpus = [line for line in lspci_output.splitlines() if "AMD" in line and "VGA" in line]
                if amd_gpus:
                    return " / ".join(amd_gpus)
            except Exception:
                pass

            if shutil.which("rocm-smi"):
                try:
                    rocm_output = subprocess.check_output(["rocm-smi", "--showproductname"], text=True)
                    rocm_lines = [line.strip() for line in rocm_output.splitlines() if "GPU" in line]
                    return " / ".join(rocm_lines) if rocm_lines else None
                except Exception:
                    return None

        # Try Apple Silicon
        if platform.system() == "Darwin" and "Apple" in platform.processor():
            return platform.processor()

        return None  # GPU not detected

    def format_specs(info_dict):
        lines = []
        for k, v in info_dict.items():
            lines.append(f"- **{k}**: {v}")
        return "\n".join(lines) + "\n"

    info = {}
    
    # Basic OS and Python
    info["OS"] = f"{platform.system()} {platform.release()} ({platform.version()})"
   
    # CPU
    cpu = cpuinfo.get_cpu_info()
    info["CPU"] = cpu.get("brand_raw", platform.processor() or "Unknown")
    info["Cores (Physical)"] = psutil.cpu_count(logical=False)
    info["Cores (Logical)"] = psutil.cpu_count(logical=True)

    # RAM
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    info["RAM"] = f"{ram_gb:.2f} GB"

    # GPU detection
    gpu_info = detect_gpu()
    if gpu_info:
        info["GPU"] = gpu_info

    # Timestamp
    info["Collected On"] = datetime.now().isoformat()

    section_text = format_specs(info)

    return section_text 
