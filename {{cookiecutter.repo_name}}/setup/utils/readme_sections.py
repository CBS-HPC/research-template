import os
import json
import re
import os
import json
import platform

from .general_tools import *
from .toml_tools import *


def main_text(project_name,project_description,contact,system_spec,py_version,code_path,software_version,activate,ci_tools,cli_tools,config,install,usage,dcas):

    # Project header
    header = f"""# {project_name}

{project_description}

## 📇 Contact Information

{contact}

<a name="system-and-environment-information"></a>
<details>
<summary>📋 System and Environment Information</summary>

The project was developed and tested on the following operating system:

{system_spec}

The environments were set up using:

- **Project setup scripts** (`./setup`) installed with **{py_version}**
- **Project code** (`{code_path}`) installed with **{software_version}**

Further details can be found in the [Installation](#installation) section.

</details>

<a name="project-activation"></a>
<details>
<summary>🚀 Project Activation</summary>

To configure the project's environment—including project paths, environment variables, and virtual environments—follow the steps below. These configurations are defined in the `.env` file.

> ⚠️ The `.env` file is excluded from this repository for security reasons. To replicate the environment, please follow the instructions in the [Installation](#installation) section.

{activate}

</details>

<a name="unit-test-ci"></a>
<details>
<summary>📅 Unit Testing and Continuous Integration (CI)</summary>

{ci_tools}

</details>

<a name="cli-tools"></a>
<details>
<summary>🔧 CLI Tools</summary>

{cli_tools}

</details>

<a name="configuration-files-root-level"></a>
<details>
<summary>🗂️ Configuration Files (Root-Level)</summary>

{config}

</details>

<a name="installation"></a>
<details>
<summary>💻 Installation</summary>

Follow these steps to set up the project on your local machine:

{install}

</details>

<a name="script-structure-and-usage"></a>
<details>
<summary>📜 Script Structure and Usage</summary>

{usage}

</details>

<a name="dataset-list"></a>
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

<a name="code--dataset-network-analysis"></a>
<details>
<summary>Code & Dataset Network Analysis</summary>

</details>

<a name="project-directory-structure"></a>
<details>
<summary>📁 Project Directory Structure</summary>

The current repository structure is shown in the tree below, and descriptions for each file can be found or edited in the `./pyproject.toml` file.

```

```

</details>

<a name="creating-a-replication-package-based-on-dcas"></a>
<details>
<summary>📚 Creating a Replication Package Based on DCAS</summary>

{dcas}

</details>
"""
    return header

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

def set_setup(programming_language,py_version,software_version,conda_version,pip_version,uv_version,repo_name, repo_user,hostname):            
    setup = ""

    if repo_name and repo_user:
        setup += "### Clone the Project Repository\n"
        "This will donwload the repository to your local machine. '.env' file is not include in the online repository.\n"
        "Clone the repository using the following command:\n"
        setup += "```\n"
        if hostname:
            setup += (f"git clone https://{hostname}/{repo_user}/{repo_name}.git\n"   
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

    setup += "#### Install using uv :\n"
    setup += f"If you prefer a faster and more reproducible alternative to pip, you can use **[{uv_version}](https://github.com/astral-sh/uv)** with **{py_version}** to install the dependencies from `requirements.txt`:\n"
    setup += "```\n"
    setup += "uv pip install -r requirements.txt\n"
    setup += "```\n\n"
    setup += "> 💡 [uv](https://github.com/astral-sh/uv) provides faster installs and better reproducibility by resolving and locking dependencies consistently. Install it with `pip install uv` or follow the [official instructions](https://github.com/astral-sh/uv).\n\n"


    if programming_language.lower() == "r":
        setup += f"> ⚡ Note: Pip or uv installation will **not** install **{software_version}**.\n\n"


    
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
        setup += f"The project's environment is based on **{software_version}**. R package dependencies can be installed within the `/R` directory using the `renv` package and the provided lock file (`renv.lock`):\n\n"
        setup += "```\n"
        setup += "cd R\n\n"
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

def set_script_structure(programming_language, software_version, folder_path, json_file = "./file_description.json"):
    """
    Generate the README section for Script Structure and Usage based on the programming language.

    Args:
        programming_language (str): One of ['r', 'python', 'stata', 'matlab', 'sas']
        software_version (str): Version string for the language/runtime (e.g. "Python 3.11")
        folder_path (str): Path to search for numbered scripts

    Returns:
        str: Formatted markdown for inclusion in your README
    """

    def find_scripts(folder_path, source_ext, notebook_ext):
        """
        Recursively find and return ordered scripts in folder_path matching the given
        source and notebook extensions. Scripts are sorted by their two-digit numeric prefix.
        
        Returns a list of tuples: (kind, full_path), where kind is 'source' or 'notebook'.
        """
        # Ensure notebook_exts is a list
        if isinstance(notebook_ext, str):
            notebook_exts = [notebook_ext.lower()]
        else:
            notebook_exts = [ext.lower() for ext in notebook_ext]

        prefix_pattern = re.compile(r'^s(\d{2})_', re.IGNORECASE)
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

                m = prefix_pattern.match(fn)
                if not m:
                    continue
                prefix = int(m.group(1))
                found.append((prefix, kind, os.path.join(root, fn)))

        # sort by prefix then drop prefix
        found.sort(key=lambda x: x[0])
        return [(kind, path) for _, kind, path in found]

            # Load descriptions JSON
    
    file_descriptions = read_toml_json(json_filename = json_file, tool_name = "file_descriptions", toml_path = "pyproject.toml")  

    if not file_descriptions:
        file_descriptions = {}

    #if os.path.exists(json_file):
    #    with open(json_file, "r", encoding="utf-8") as jf:
    #        file_descriptions = json.load(jf)
    #else:
    #    file_descriptions = {}

    programming_language = programming_language.lower()
    if programming_language not in ["r", "python", "stata", "matlab", "sas"]:
        raise ValueError("Supported programming languages are: r, python, stata, matlab, sas.")

    # set extensions
    if programming_language == "r":
        source_ext, notebook_ext = ".R", ".Rmd"
    elif programming_language == "python":
        source_ext, notebook_ext = ".py", ".ipynb"
    elif programming_language == "stata":
        source_ext, notebook_ext = ".do", ".ipynb"
    elif programming_language == "matlab":
        source_ext, notebook_ext = ".m", [".ipynb", ".mlx"]
    else:  # sas
        source_ext, notebook_ext = ".sas", ".ipynb"

    scripts = find_scripts(folder_path, source_ext, notebook_ext)

    # collect all orchestration candidates, then pick the first
    orch_candidates = [
        path for kind, path in scripts
        if kind == "source" and os.path.basename(path).lower().startswith("s00_")
    ]
    orchestrator = orch_candidates[0] if orch_candidates else None

    # collect all notebook candidates, then pick the first
    nb_candidates = [
        path for kind, path in scripts
        if kind == "notebook" and os.path.basename(path).lower().startswith("s00_")
    ]
    notebook = nb_candidates[0] if nb_candidates else None

    code_path = language_dirs.get(programming_language)

    md = []
    md.append(f"The project is written in **{software_version}** and includes modular scripts for standardized workflows, organized under `{code_path}`.\n")
    md.append("### Scripts Detected in Workflow:\n")
    for kind, path in scripts:
        name = os.path.basename(path)
        display = os.path.splitext(os.path.basename(path))[0]
        display = display.replace("_", " ").title()
        filename = os.path.basename(path)
        desc = file_descriptions.get(filename)
        if desc:
            md.append(f"- **{display}** (`{name}`) — {desc}")
        else:
            md.append(f"- **{display}** (`{name}`) — `{path}`")
    md.append("")

    if any("utils" in os.path.basename(p).lower() for _, p in scripts):
        md.append("🛠️ **Note**: `utils` does not define a `main()` function and should not be executed directly.\n")

    md.append("### Execution Options:\n")
    if orchestrator:
        md.append(f"**Run the full pipeline via the orchestration script:**\n")
        md.append(f"\n `{os.path.basename(orchestrator)}`:\n")
        try:
            code = open(orchestrator, encoding="utf-8").read().rstrip()
            md.append(f"```{programming_language.lower()}\n{code}\n```")
        except Exception as e:
            md.append(f"_Failed to read orchestrator script: {e}_")
    else:
        md.append("_No orchestration script (`00_…`) found._")

    return "\n".join(md)

def set_config_table(programming_language):

    if programming_language.lower() != "r":
        config = """The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.
| File                    | Purpose                                                                                         |
|-------------------------|-------------------------------------------------------------------------------------------------|
| `.gitignore`            | Excludes unnecessary files from Git version control                                             |
| `.env`                  | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `environment.yml`       | Conda environment definition for Python/R, including packages and versions                      |
| `requirements.txt`      | Pip-based Python dependencies for lightweight environments                                      |
""" 
    else:
        config = """The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.

| File                    | Purpose                                                                                         |
|-------------------------|-------------------------------------------------------------------------------------------------|
| `.gitignore`            | Excludes unnecessary files from Git version control                                             |
| `.env`                  | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `environment.yml`       | Conda environment definition for Python/R, including packages and versions                      |
| `requirements.txt`      | Pip-based Python dependencies for lightweight environments                                      |
| `renv.lock`             | Records the exact versions of R packages used in the project                                    |
""" 
    return config

def set_cli_tools(programming_language):

    code_path = language_dirs.get(programming_language.lower())

    cli_tools = f"""
The `setup` Python package provides a collection of command-line utilities to support project configuration, dependency management, documentation, and reproducibility workflows.

> ℹ️ **Note**: To use these commands, you must first install the local `setup` package.  
> Refer to the [Installation](#installation) section for details on how to install it using `pip install -e .` from the `setup/` directory.

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

### 🛠️ Usage

After activating your environment, run commands like:

```
run-setup
set-dataset
update-requirements
```
"""
    return cli_tools

def set_ci_tools(programming_language: str, code_repo: str):
    pl = programming_language.lower()
    repo = code_repo.lower()

    lang_info = {
        "python": {
            "test_framework": "`pytest`",
            "code_folder": "`src/`",
            "test_folder": "`tests/`",
            "test_format": "`test_*.py`",
            "package_file": "`requirements.txt`",
            "example": """Project structure:

```
src/s00_main.py
tests/test_s00_main.py
```

Run tests:

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
            "example": """Project structure:

```
R/s00_main.R
tests/testthat/test-s00_main.R
```

Run tests:

```
testthat::test_dir("tests/testthat")
```

From command line:

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
            "example": """Project structure:

```
src/s00_main.m
tests/test_s00_main.m
```

Run tests in MATLAB:

```
results = runtests('tests');
assert(all([results.Passed]), 'Some tests failed')
```

From command line:

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
            "example": """Project structure:

```
stata/do/s00_main.do
tests/test_s00_main.do
```

Run tests in Stata:

```
do tests/test_s00_main.do
```

Or in batch mode:

```
stata -b do tests/test_s00_main.do
```
"""
        }
    }

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

    if pl not in lang_info:
        return f"Unsupported language: {programming_language}"
    if repo not in ci_matrix:
        return f"Unsupported code repository: {code_repo}"
    if pl not in ci_matrix[repo]["supports"]:
        return f"{programming_language.capitalize()} is not supported on {code_repo.capitalize()}."

    lang = lang_info[pl]
    ci = ci_matrix[repo]

    if lang['package_file']:
        pipeline = f"""Each pipeline:
1. Installs language runtime and dependencies
2. Installs project packages using {lang['package_file']}
3. Runs tests in `tests/`
4. Outputs results and logs"""
    else:
        pipeline = f"""Each pipeline:
1. Installs language runtime and dependencies
2. Runs tests in `tests/`
3. Outputs results and logs"""


    section = f"""This template includes built-in support for **unit testing** and **CI automation** in {programming_language.capitalize()} to promote research reliability and reproducibility.

### 🧪 Unit Testing

| Language | Test Framework     | Code Folder | Test Folder       | Test File Format |
| -------- | ------------------ | ----------- | ----------------- | ---------------- |
| {programming_language.capitalize()}   | {lang['test_framework']} | {lang['code_folder']} | {lang['test_folder']} | {lang['test_format']} |

Tests are automatically scaffolded to match your workflow scripts (e.g., `s00_main`, `s04_preprocessing`). They can be run locally, in CI, or as part of a pipeline.

{lang['example']}

### ⚙️ Continuous Integration (CI)

CI is configured for **{code_repo.capitalize()}** with **{programming_language.capitalize()}** support.

Config file: `{ci['config_file']}`

{pipeline}

{ci['note']}
"""
    return section.strip()

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
