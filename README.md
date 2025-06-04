# 🧪 Reproducible Research Template: Structured Workflows and Replication Packages

![Repo size](https://img.shields.io/github/repo-size/CBS-HPC/research-template)
![Last commit](https://img.shields.io/github/last-commit/CBS-HPC/research-template)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC--BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
![Open issues](https://img.shields.io/github/issues/CBS-HPC/research-template)
![Pull requests](https://img.shields.io/github/issues-pr/CBS-HPC/research-template)
![Windows](https://img.shields.io/badge/tested%20on-Windows-blue?logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/tested%20on-Bash%20(Ubuntu)-blue?logo=linux&logoColor=white)


> ⚠️ **This repository is under active development. Features, structure, and documentation may change.**

This project template is designed to help **CBS researchers** create structured, automated, and publication-ready workflows aligned with the principles of **Open Science** and **FAIR** data practices (Findable, Accessible, Interoperable, and Reusable).

Built with [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/), the template supports **Python**, **R**, **Stata** and **Matlab**, and provides an integrated framework for organizing code, managing datasets, tracking dependencies, enabling version control, and backing up research securely.

Whether you're preparing a replication package for publication, submitting data and code for peer review, or organizing internal research, this tool helps you streamline reproducible research workflows tailored to the needs of the **CBS research community**.

> ✅ This template has been tested on **Windows (PowerShell)** and **Ubuntu (bash)** environments.

---

🔍 **Key features:**

- 📁 Effective project structure for transparent and consistent workflows  
- 🧬 Multi-language support: Python, R, Stata and Matlab 
- 🗃️ Version control via Git, Datalad, or DVC  
- 📦 Automated script scaffolding for analysis, modeling, and visualization  
- 🔐 Environment management via Conda or venv  
- ☁️ Backup integration with DeiC Storage, Dropbox, and OneDrive  
- 🚀 Remote repository setup with GitHub, GitLab, or Codeberg  
- 🧾 Auto-generated metadata files: `README.md`, `LICENSE.txt`, `CITATION.cff`  
- 🧰 Installation guides and activation scripts for both Windows and Bash  
- 📑 Structured documentation of all files, code, and datasets
- 📄 Support for DCAS-aligned replication packages  

This template is developed and maintained by the **CBS High-Performance Computing (HPC)** team to promote reproducibility, collaboration, and compliance in computational research at Copenhagen Business School.

---

## 🛠️ Requirements

- [**Python 3.9+**](https://www.python.org/downloads/) – Required to run the template and environment setup scripts  
- [**cookiecutter**](https://cookiecutter.readthedocs.io/en/latest/) – Used to generate the project structure  
- [**Git**](https://git-scm.com/downloads) *(optional)* – Git is optional for project generation but **required** if using version control or pushing to remote repositories.

Install Cookiecutter:

```bash
pip install cookiecutter
```

> If Git or other tools are missing, the template will offer to download and configure them for you.

---

## 🏗️ Generate a New Project

This template can be used either online (via GitHub) or offline (manually downloaded).

<details>
<summary>📦 Online (with Git)</summary>

Use this option if Git is installed and you want to fetch the template directly from GitHub:

```bash
cookiecutter gh:CBS-HPC/research-template
```

</details>

<details>
<summary>📁 Offline (Local Installation)</summary>

If Git is **not installed**, you can still use the template by downloading it manually:

1. Go to [https://github.com/CBS-HPC/research-template](https://github.com/CBS-HPC/research-template)  
2. Click the green **“Code”** button, then choose **“Download ZIP”**  
3. Extract the ZIP file to a folder of your choice  
4. Run Cookiecutter locally:

```bash
cookiecutter path/to/research-template
```

> ⚠️ Do **not** use `git clone` if Git is not installed. Manual download is required in this case.

</details>

---

## 🧾 Setup Options

This template guides you through a series of interactive prompts to configure your project—including version control, environment setup, backup destinations, and remote repository platforms. Click below to expand each section for a visual breakdown of all setup steps.

<details>
<summary>📦 Project Metadata</summary>

Provide core metadata for your project—used for naming, documentation, citation, and licensing.

```
├── project_name              → Human-readable name
├── repo_name                 → Folder and repository name
├── description               → Short summary of the project
├── author_name               → Your full name
├── email                     → Your CBS email
├── orcid                     → Your ORCID researcher ID
├── version                   → Initial version number (e.g., 0.0.1)
├── code_license              → [MIT | BSD-3-Clause | Apache-2.0 | None]
├── documentation_license     → [CC-BY-4.0 | CC0-1.0 | None]
├── data_license              → [CC-BY-4.0 | CC0-1.0 | None]
```

This information is used to auto-generate:

- `README.md` – populated with title, description, and author info  
- `LICENSE.txt` – includes license sections for code, documentation, and data  
- `CITATION.cff` – for machine-readable academic citation


### 🔑 License Descriptions

**Code Licenses:**

- [**MIT**](https://opensource.org/licenses/MIT) – Very permissive, short license. Allows reuse with attribution.  
- [**BSD-3-Clause**](https://opensource.org/license/bsd-3-clause/) – Permissive, but includes a non-endorsement clause.  
- [**Apache-2.0**](https://www.apache.org/licenses/LICENSE-2.0) – Like MIT, but includes explicit patent protection.  

**Documentation Licenses:**

- [**CC-BY-4.0**](https://creativecommons.org/licenses/by/4.0/) – Requires attribution, allows commercial and derivative use.  
- [**CC0-1.0**](https://creativecommons.org/publicdomain/zero/1.0/) – Places documentation in the public domain (no attribution required).

**Data Licenses:**

- [**CC-BY-4.0**](https://creativecommons.org/licenses/by/4.0/) – Allows reuse and redistribution with attribution.  
- [**CC0-1.0**](https://creativecommons.org/publicdomain/zero/1.0/) – Public domain dedication for unrestricted reuse.

> ℹ️ If “None” is selected, the corresponding section will be omitted from the LICENSE file.

</details>

<details>
<summary>🧬 Programming Language & Script Templates</summary>

Choose your primary scripting language. The template supports multi-language projects and automatically generates a modular codebase tailored to your selection.

```
├── programming_language      → [Python | R | Stata | Matlab | None]
│   └── If R/Stata/Matlab selected:
│       └── Prompt for executable path if not auto-detected
```

If you select **R**, **Stata** or **Matlab** the template will prompt for the path to the installed software if it is not auto-detected.

### 🛠️ Script Generation

Script generation is **language-agnostic**: based on your selected language, the template will create files with the appropriate extensions:

- `.py` (scripts) and `.ipynb` (notebooks) for Python
- `.R` (scripts) and `.Rmd` (notebooks) for R
- `.m`(scripts) and `.mlx` (notebooks) for Matlab 
- `.do` (scripts) and `.ipynb` (notebooks) for Stata


These starter scripts are placed in the `src/` directory and include:

```
├── s00_main.*                  → orchestrates the full pipeline
├── s00_workflow.*              → notebook (.ipynb, .Rmd, .mlx) orchestrating the full pipeline
├── s01_install_dependencies.*  → installs any missing packages required for the project
├── s02_utils.*                 → shared helper functions (not directly executable)
├── s03_data_collection.*       → imports or generates raw data
├── s04_preprocessing.*         → cleans and transforms data
├── s05_modeling.*              → fits models and generates outputs
├── s06_visualization.*         → creates plots and summaries
├── get_dependencies.*          → retrieves and checks required dependencies for the project environment. (Utilised)

```

Each script is structured to:

- Define a `main()` function or logical entry point (where applicable)  
- Automatically resolve project folder paths (`data/00_raw/`, `results/figures/`, etc.)  
- Remain passive unless directly called or imported  
- Support reproducible workflows by default

> 🧩 Scripts are designed to be flexible and modular: you can run them individually, chain them in `main.*`, or explore them interactively using Jupyter or RMarkdown.

</details>

<details>
<summary>🧪 Environment Configuration</summary>

Set up isolated virtual environments using **Conda**, **venv**, or your system’s **base installation**.

```
├── R environment (if R used)
│   └── env_manager_r         → [Conda | Base Installation]
│       ├── If Conda:         → Prompt for R version
│       └── If Base:          → Uses system-installed R
├── Python environment
│   └── env_manager_python    → [Conda | Venv | Base Installation]
│       ├── If Conda:         → Prompt for Python version
│       ├── If Venv:          → Uses current Python kernel version
│       └── If Base:          → Uses system-installed Python
├── Proprietary software (if selected)
│   └── [Stata | Matlab | R]
│       ├── Searches system PATH for installed application
│       └── Prompts user for executable path if not found
```

**Environment manager options:**

- [**Conda**](https://docs.conda.io/en/latest/) – A popular environment and package manager that supports both Python and R. Enables exact version control and cross-platform reproducibility.  
- [**venv**](https://docs.python.org/3/library/venv.html) – Python’s built-in tool for creating lightweight, isolated environments. Ideal for Python-only projects.  
- **Base Installation** – No virtual environment is created. Dependencies are installed directly into your system-wide Python or R installation.

Regardless of your choice, the following files are generated to document your environment:

- `environment.yml` – Conda-compatible list of dependencies  
- `requirements.txt` – pip-compatible Python package list  
- `renv.lock` – (if R is selected) snapshot of R packages using the `renv` package  

> ⚠️ When using **venv** or **base installation**, the `environment.yml` file is created **without Conda's native environment tracking**. As a result, it may be **less accurate or reproducible** than environments created with Conda.  
> ⚠️ If proprietary software (e.g., Stata, Matlab, R) is selected, the system will first **search your PATH**. If not found, you’ll be prompted to manually enter the executable path.  
> 💡 Conda will be downloaded and installed automatically if it's not already available.

</details>


<details>
<summary>🗃️ Version Control</summary>

Choose a system to version your code (and optionally your data).

```
├── version_control           → [Git | Datalad | DVC | None]
│   ├── Git:
│   │   ├── Prompt for Git user.name and user.email
│   │   ├── Initializes Git repo in project root
│   │   └── Initializes separate Git repo in `data/`
│   ├── Datalad:
│   │   ├── Initializes Git repo (if not already)
│   │   └── Initializes a Datalad dataset in `data/` (nested Git repo)
│   └── DVC:
│       ├── Initializes Git repo (if not already)
│       ├── Runs `dvc init` to create a DVC project
│       └── Configures `data/` as a DVC-tracked directory
```

This template supports several version control systems to suit different workflows:

- [**Git**](https://git-scm.com/) – general-purpose version control for code and text files  
- [**Datalad**](https://www.datalad.org/) – for data-heavy, file-based versioning; designed to support **FAIR** principles and **Open Science** workflows  
- [**DVC**](https://dvc.org/) – for machine learning pipelines, dataset tracking, and model versioning

### 🔧 How it works:

- **Git**: initializes the project root as a Git repository  
  - Also creates a separate Git repo in `data/` to track datasets independently  
- **Datalad**: builds on Git by creating a [Datalad dataset](https://handbook.datalad.org/en/latest/basics/101-137-datasets.html) in `data/`  
- **DVC**: runs `dvc init` and sets up `data/` as a [DVC-tracked directory](https://dvc.org/doc/start/data-management) using external storage and `.dvc` files

### 📝 Auto-generated `.gitignore` includes:

```
├── data/                  → 00_raw, 01_interim and 02_processed data folders
├── bin/                   → local binaries (e.g., rclone)
├── env/, __pycache__/     → Python virtual environments and caches
├── .vscode/, .idea/       → IDE and editor configs
├── .DS_Store, *.swp       → OS/system-generated files
├── .ipynb_checkpoints/    → Jupyter notebook checkpoints
├── .coverage, *.log       → logs, test coverage reports
```

> 🧹 These defaults help keep your repository clean, portable, and reproducible.

> ⚙️ If **Git**, **Datalad**, or **DVC** (or their dependencies) are not detected, the template will automatically download and install them during setup.
> This ensures you can use advanced version control tools without manual pre-installation.
</details>

<details>
<summary>☁️ Backup with Rclone</summary>

This template supports automated backup to **CBS-approved storage solutions** using [`rclone`](https://rclone.org).

```
├── remote_backup             → [DeIC | Dropbox | OneDrive | Local | Multiple | None]
│   ├── DeIC:
│   │   ├── Prompt for CBS email
│   │   └── Prompt for password (encrypted)
│   ├── Dropbox / OneDrive:
│   │   ├── Prompt for email
│   │   └── Prompt for password (encrypted)
│   ├── Local:
│   │   └── Prompt to choose a local destination path
│   └── Multiple:
│       └── Allows choosing several of the above
```

Supported backup targets include:

- [**DeIC Storage**](https://storage.deic.dk/) – configured via **SFTP with password and MFA** (see instructions under “Setup → SFTP”)  
- [**Dropbox**](https://www.dropbox.com/)  
- [**OneDrive**](https://onedrive.live.com/)  
- **Local** storage – backup to a folder on your own system  
- **Multiple** – select any combination of the above

> 🔐 All credentials are stored in `rclone.conf`.  
> ☁️ `rclone` is automatically downloaded and installed if not already available on your system.

</details>

<details>
<summary>📡 Remote Repository Setup</summary>

Automatically create and push to a Git repository on a remote hosting platform.

```
├── remote_repo               → [GitHub | GitLab | Codeberg | None]
│   └── If selected:
│       ├── Prompt for username
│       ├── Choose visibility: [private | public]
│       └── Provide personal access token (stored in `.env`)
```

Supported platforms include:

- [**GitHub**](https://github.com) – the most widely used platform for open source and academic collaboration. Supports seamless repo creation, authentication, and automation.
- [**GitLab**](https://gitlab.com) – a DevOps platform that supports both self-hosted and cloud-hosted repositories. Ideal for collaborative development with built-in CI/CD pipelines.
- [**Codeberg**](https://codeberg.org) – a privacy-focused Git hosting service powered by [Gitea](https://about.gitea.com). Community-driven and compliant with European data governance standards.

Repositories are created using the **HTTPS API**, and authenticated with **personal access tokens**.

> 🛡️ Your credentials and tokens are securely stored in the `.env` file and never exposed in plain text.

</details>

---
## 🧾 Project Structure and Usage

This template generates a standardized, reproducible project layout. It separates raw data, code, documentation, setup scripts, and outputs to support collaboration, transparency, and automation.

<details>
<summary>📁 Directory Structure</summary>

You can find or update human-readable file descriptions in `file_descriptions.json`.

```
├── .cookiecutter             # Cookiecutter configuration used to generate this project
├── .git                      # Git repository metadata
├── .gitignore                # Files/directories excluded from Git version control
├── .rcloneignore             # Files/directories excluded from Rclone backup
├── .treeignore               # Files excluded from file tree utilities or visualizations
├── CITATION.cff              # Machine-readable citation metadata for scholarly reference
├── DCAS template/            # Template for DCAS-compliant replication packages
│   └── README.md             # README for the DCAS template
├── LICENSE.txt               # Project license file
├── README.md                 # Main README with usage and documentation
├── activate.*                # Script to activate the environment (either `.ps1` or `.sh`)
├── deactivate.*              # Script to deactivate the environment (either `.ps1` or `.sh`)
├── bin/                      # Local tools (e.g., rclone binaries, installers)
├── data/                     # Structured project data directory
│   ├── .git/                 # Standalone Git repo for tracking datasets
│   ├── .gitlog               # Git log for the data repository
│   ├── 00_raw/                  # Original, immutable input data
│   ├── 01_interim/              # Intermediate data created during processing
│   └── 02_processed/            # Final, clean data ready for analysis
├── docs/                     # Project documentation, reports, or rendered outputs
├── environment.yml           # Conda-compatible environment definition (Python/R)
├── file_descriptions.json    # JSON file with editable descriptions for all project files
├── requirements.txt          # pip-compatible list of Python dependencies
├── results/                  # Results generated by the project
│   └── figures/              # Charts, plots, and other visual outputs
├── setup/                    # Internal setup module for environment config and CLI tools
│   ├── dependencies.txt      # List of Python dependencies for `setup` module  
│   ├── setup.py              # Setup script to register the project as a Python package
│   └── utils/                # Utility functions and scripts for environment setup
└── src (R/stata)/                  # Source code for data processing, analysis, and reporting
    ├── dependencies.txt            # List of dependencies for `src` module  
    ├── get_dependencies.*          # retrieves and checks required packages required for the project (Utilised)
    ├── s00_main.*                  # Orchestrates the full workflow pipeline
    ├── s00_workflow.*              # Interactive workflow (e.g., Jupyter notebook or RMarkdown)
    ├── s01_install_dependencies.*  # Installs any missing packages required for the project
    ├── s02_utils.*                 # Shared helper functions for reuse across script
    ├── s03_data_collection.*       # Imports or generates raw data from external sources
    ├── get_dependencies.*          # retrieves and checks required packages required for the project (Utilised)
    ├── s04_preprocessing.*         # Cleans and transforms raw input data
    ├── s05_modeling.*              # Performs modeling, estimation, or machine learning
    ├── s06_visualization.*         # Creates plots, charts, and visual summaries
```


> 🔁 `activate.*` and `deactivate.*` are either PowerShell (`.ps1`) or Bash (`.sh`) scripts, depending on your platform (Windows or macOS/Linux).

> ✳️ Script file extensions (`.py`, `.R`, `.do`, `.m`) are determined by the programming language selected during project setup.

</details>

<details>
<summary>🚀 Project Activation</summary>

To configure the project's environment—including project paths, environment variables, and virtual environments—run the activation script for your operating system. These scripts read settings from the `.env` file.

### 🪟 Windows (PowerShell)

**Activate:**

```powershell
./activate.ps1
```

**Deactivate:**

```powershell
./deactivate.ps1
```

### 🐧 macOS / Linux (bash)

**Activate:**

```bash
source activate.sh
```

**Deactivate:**

```bash
source deactivate.sh
```

</details>

<details>
<summary>📅 Unit Testing and Continuous Integration (CI)</summary>

This template includes built-in support for **unit testing** and **CI automation** across Python, R, MATLAB, and Stata to promote research reliability and reproducibility.

---

### 🧪 Unit Testing

Unit test files are automatically generated for core analysis scripts and placed in a unified `tests/` folder during setup. The structure varies slightly by language:

| Language | Test Framework     | Code Folder | Test Folder       | Test File Format |
| -------- | ------------------ | ----------- | ----------------- | ---------------- |
| Python   | `pytest`           | `src/`      | `tests/`          | `test_*.py`      |
| R        | `testthat`         | `R/`        | `tests/testthat/` | `test-*.R`       |
| MATLAB   | `matlab.unittest`  | `src/`      | `tests/`          | `test_*.m`       |
| Stata    | `.do` script-based | `stata/do/` | `tests/`          | `test_*.do`      |

Tests are automatically scaffolded to match your workflow scripts (e.g., `s00_main`, `s04_preprocessing`). They can be run locally, in CI, or as part of a pipeline.

---

### 📄 Example Layouts and Test Commands

**Python**

Project structure:
```
src/s00_main.py
tests/test_s00_main.py
```

Run tests:
```
pytest
```

**R**
Project structure:
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

**Matlab**
Project structure:
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

**Stata**
Project structure:
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

### 🧪 Test Development Guidelines

Writing good tests ensures that your code behaves as expected and simplifies debugging and maintenance.

Here are best practices for test development:

- ✅ Focus on **core logic and data transformations** — test data cleaning, modeling, and utility functions.
- ✅ Include **edge cases** — e.g., missing values, invalid inputs, or empty datasets.
- ✅ Keep tests **independent and repeatable** — don’t rely on external state or prior test outcomes.
- ✅ Use **assertions appropriate for your language**:
  - `assert` in Python
  - `expect_equal()`, `expect_error()` in R/testthat
  - `verifyEqual()`, `verifyTrue()` in MATLAB
  - `assert` in Stata
- ✅ Organize tests to mirror your codebase (e.g., `s05_modeling.py` → `test_s05_modeling.py`)

> 🧪 Tests don’t need to be exhaustive — aim for **critical correctness** and **reproducibility**.

---

### 🔧 Test-Driven Development (TDD)

Test-Driven Development (TDD) is a workflow that emphasizes writing tests **before** writing the actual implementation. It's especially useful for ensuring reproducibility and correctness in research workflows.

**TDD workflow:**
1. **Write a failing test** that describes the desired behavior
2. **Implement the minimum code** needed to make the test pass
3. **Refactor** the implementation (if needed) while keeping the test green

**Benefits in research projects:**
- Ensures reproducible and validated results
- Encourages modular, testable code
- Prevents regressions when modifying scripts

> 💡 TDD fits naturally with script scaffolding in this template. Each script has a corresponding test file scaffold to encourage this workflow.

---

### ⚙️ Continuous Integration (CI)

The template supports CI pipelines on all major platforms:

- **GitHub Actions**
- **GitLab CI/CD**
- **Codeberg CI** (via Woodpecker)

CI configurations are auto-generated based on your language and repository host, and placed in the appropriate file:

| Platform | Config File                |
| -------- | -------------------------- |
| GitHub   | `.github/workflows/ci.yml` |
| GitLab   | `.gitlab-ci.yml`           |
| Codeberg | `.woodpecker.yml`          |

Each pipeline performs the following:

1. Installs the appropriate language environment
2. Installs dependencies (e.g., `requirements.txt`, `renv.lock`)
3. Runs tests in the `tests/` directory
4. Outputs test logs and error reports

For R projects, CI will run `renv::restore(project = 'R')` if `R/renv.lock` exists. Otherwise, it falls back to `install.packages()`.

---

### 🔄 CI Config via CLI

CI can be configured to the selected platform using the built-in CLI command:

```
ci_config 
```

This works by renaming .yml files to .yml.disabled and back. It's useful for disabling CI during development
  
  🚪 CI is disabled by default after project generation. Use ci-config --enable when you're ready to activate it.


### 🔄 CI Control via CLI

CI can be toggled on or off using the built-in CLI command:

```
ci_control --enable 
ci_control --disable 
```

</details>


<details>
<summary>🔧 CLI Tools</summary>

The `setup` Python package provides a collection of command-line utilities to support project configuration, dependency management, documentation, and reproducibility workflows.

> ℹ️ **Note**: The `setup` package is **automatically installed** during project setup.  
> You can also manually install or reinstall it using:  
> `pip install -e ./setup`

Once installed, the following CLI commands become available from the terminal:

| Command                     | Description                                                                                       |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| `push-backup`                | Executes a full project backup using preconfigured rules and paths.                               |
| `set-dataset`               | Initializes or registers datasets (e.g., add metadata, sync folders).                            |
| `update-dependencies`       | Retrieves and updates Python and R dependencies listed in `setup/` and `src/`.                   |
| `run-setup` *(in progress)* | Main entry point to initialize or reconfigure the project environment.                           |
| `update-readme`             | Regenerates the `README.md` with updated metadata and file structure.                            |
| `reset-templates`           | Resets or regenerates script templates in `src/` based on project language.                      |
| `code-examples`             | Generates language-specific example code and notebooks (Python, R, etc.).                   |
| `dcas-migrate` *(in progress)* | Validates and migrates the project structure to DCAS (Data and Code Availability Standard) format. |

### 🛠️ Usage

After activating your environment, run commands like:

```bash
run-setup
set-dataset
update-requirements
```

</details>

<details>
<summary>🗂️ Configuration Files (Root-Level)</summary>

The following configuration files are placed in the root directory and used by tools for managing environments, templates, backups, and project metadata.

| File                      | Purpose                                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| `.gitignore`              | Excludes unnecessary files from Git version control                                                 |
| `.rcloneignore`           | Excludes files and folders from Rclone-based backups                                                |
| `.treeignore`             | Filters out directories from project tree visualizations                                            |
| `.cookiecutter`           | Cookiecutter metadata for project initialization                                                    |
| `.env`                    | Defines environment-specific variables (e.g., paths, tokens, settings); typically excluded from Git |
| `environment.yml`         | Conda environment definition for installing Python and R dependencies                               |
| `requirements.txt`        | pip-compatible Python dependencies                                                                  |
| `renv.lock`               | Captures exact versions of R packages used (if R is selected)                                       |
| `file_descriptions.json`  | JSON file containing editable metadata for the directory structure; used by setup and documentation tools |

</details>

---

## 📚 DCAS Compatibility

This template is designed to support the creation of replication packages that are fully compatible with the [Data and Code Availability Standard (DCAS)](https://datacodestandard.org/), a widely endorsed initiative to promote transparency and reproducibility in social science research.

By structuring code, data, metadata, and documentation into clear, well-separated folders—with standard naming conventions, licensing, and README scaffolds—the template helps you align with the expectations of journals that require or recommend DCAS compliance.

Key features that support DCAS alignment:

- 📂 Separation of raw, interim, and processed data
- 📜 Auto-generated licensing and citation metadata (`LICENSE.txt`, `CITATION.cff`)
- 📑 Structured file annotations via `file_descriptions.json`
- 🧪 Scripted environment setup and reproducibility utilities
- 📄 Optional DCAS template folder with journal-ready content

This format is consistent with the [AEA Data Editor’s guidance](https://aeadataeditor.github.io/aea-de-guidance/preparing-for-data-deposit.html) and the broader Social Science Data Editors' best practices.

**Examples of journals endorsing the DCAS standard:**

- [American Economic Journal: Applied Economics](https://www.aeaweb.org/journals/applied-economics)
- [Econometrica](https://www.econometricsociety.org/publications/econometrica)
- [Economic Inquiry](https://onlinelibrary.wiley.com/journal/14680299)
- [Journal of Economic Perspectives](https://www.aeaweb.org/journals/jep)

For a full list of supporting journals, visit the [DCAS website](https://datacodestandard.org/journals/).

> 📝 Journal-specific requirements may vary—always consult their latest submission guidelines to ensure full compliance.


---

## 🙏 Acknowledgements

This project was inspired by:

- [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/)

Maintained by the **CBS High-Performance Computing (HPC)** team.

---

## 📬 Support

For questions, suggestions, or bug reports:

- Open an [Issue on GitHub](https://github.com/CBS-HPC/replication_package/issues)
- Or contact: [kgp.lib@cbs.dk](mailto:kgp.lib@cbs.dk)

---
