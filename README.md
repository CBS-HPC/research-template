# 🧪 Reproducible Research Template: Structured Workflows and Replication Packages

![Repo size](https://img.shields.io/github/repo-size/CBS-HPC/research-template)
![Last commit](https://img.shields.io/github/last-commit/CBS-HPC/research-template)
![License](https://img.shields.io/github/license/CBS-HPC/research-template)
![Open issues](https://img.shields.io/github/issues/CBS-HPC/research-template)
![Pull requests](https://img.shields.io/github/issues-pr/CBS-HPC/research-template)
![Windows](https://img.shields.io/badge/tested%20on-Windows-blue?logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/tested%20on-Bash%20(Ubuntu)-blue?logo=linux&logoColor=white)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1234567.svg)](https://doi.org/10.5281/zenodo.1234567)


This project template is designed to help **CBS researchers** create structured, automated, and publication-ready workflows aligned with the principles of **Open Science** and **FAIR** data practices (Findable, Accessible, Interoperable, and Reusable).

Built with [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/), the template supports **Python**, **R**, **Stata**, **Matlab**, and **SAS**, and provides an integrated framework for organizing code, managing datasets, tracking dependencies, enabling version control, and backing up research securely.

Whether you're preparing a replication package for publication, submitting data and code for peer review, or organizing internal research, this tool helps you streamline reproducible research workflows tailored to the needs of the **CBS research community**.

> ✅ This template has been tested on **Windows (PowerShell)** and **Ubuntu (bash)** environments.

---

🔍 **Key features:**

- 📁 Effective project structure for transparent and consistent workflows  
- 🧬 Multi-language support: Python, R, Stata, Matlab, and SAS  
- 🗃️ Version control via Git, Datalad, or DVC  
- 📦 Automated script scaffolding for analysis, modeling, and visualization  
- 🔐 Environment management via Conda or venv  
- ☁️ Backup integration with DeiC Storage, Dropbox, and OneDrive  
- 🚀 Remote repository setup with GitHub, GitLab, or Codeberg  
- 📄 Support for DCAS-aligned replication packages

This template is developed and maintained by the **CBS High-Performance Computing (HPC)** team to promote reproducibility, collaboration, and compliance in computational research at Copenhagen Business School.


---

## 🛠️ Requirements

- Python 3.9+
- [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/installation.html)

Install Cookiecutter:

```
pip install cookiecutter
```

> ❗️ Git is optional for template usage but required if pushing to a remote repository. The template can download and install Git, Rclone, and other tools automatically if not found.

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

Provide core metadata for your project—used for naming, documentation, and citation.

```
├── project_name              → Human-readable name
├── repo_name                 → Folder and repo name
├── description               → Short project summary
├── author_name               → Your full name
├── email                     → Your CBS email
├── orcid                     → Your ORCID researcher ID
├── version                   → Initial version tag (e.g., 0.0.1)
├── open_source_license       → [MIT | BSD-3-Clause | None]
```

This information is used to auto-generate:

- `README.md` – includes your title, author, and description  
- `LICENSE.txt` – based on selected license  
- `CITATION.cff` – for machine-readable citation metadata

</details>

<details>
<summary>🧬 Programming Language & Script Templates</summary>

Choose your primary scripting language. The template supports multi-language projects and automatically generates a modular codebase tailored to your selection.

```
├── programming_language      → [Python | R | Stata | Matlab | SAS | None]
│   └── If R/Stata/Matlab/SAS selected:
│       └── Prompt for executable path if not auto-detected
```

If you select **R**, **Stata**, **Matlab**, or **SAS**, the template will prompt for the path to the installed software if it is not auto-detected.

### 🛠️ Script Generation

Script generation is **language-agnostic**: based on your selected language, the template will create files with the appropriate extensions:

- `.py` for Python  
- `.R` for R  
- `.m` for Matlab  
- `.do` for Stata  
- `.sas` for SAS  

These starter scripts are placed in the `src/` directory and include:

```
├── main.*              → orchestrates the full pipeline
├── data_collection.*   → imports or generates raw data
├── preprocessing.*     → cleans and transforms data
├── modeling.*          → fits models and generates outputs
├── visualization.*     → creates plots and summaries
├── utils.*             → shared helper functions (not directly executable)
├── workflow.ipynb      → Jupyter notebook (Python, Stata, Matlab, SAS)
├── workflow.Rmd        → RMarkdown notebook (R only)
```

Each script is structured to:

- Define a `main()` function or logical entry point (where applicable)  
- Automatically resolve project folder paths (`data/raw/`, `results/figures/`, etc.)  
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
```

**Environment manager options:**

- [**Conda**](https://docs.conda.io/en/latest/) – A popular environment and package manager that supports both Python and R. Enables exact version control and cross-platform reproducibility.  
- [**venv**](https://docs.python.org/3/library/venv.html) – Python’s built-in tool for creating lightweight, isolated environments. Ideal for Python-only projects.  
- **Base Installation** – No environment is created. Dependencies are installed directly into your system-wide Python or R installation.

Regardless of your choice, the following files are generated to document your environment:

- `environment.yml` – Conda-compatible list of dependencies  
- `requirements.txt` – pip-compatible Python package list  
- `renv.lock` – (if R is selected) snapshot of R packages using the `renv` package  

> ⚠️ When using **venv** or **base installation**, the `environment.yml` file is created **without Conda's native environment tracking**. As a result, it may be **less accurate or reproducible** than environments created with Conda.  
> 💡 Conda will be downloaded and installed automatically if it's not already available.  
> ⚠️ The template does **not install proprietary software** (e.g., Stata, Matlab, SAS). You must install these manually and provide the path when prompted.

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
├── data/                  → raw and processed data folders
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

- [**GitHub**](https://github.com) (via [GitHub CLI](https://cli.github.com)) – the most widely used platform for open source and academic collaboration. Supports seamless repo creation, authentication, and automation.
- [**GitLab**](https://gitlab.com) (via [GitLab CLI](https://gitlab.com/gitlab-org/cli)) – a DevOps platform that supports both self-hosted and cloud-hosted repositories. Ideal for collaborative development with built-in CI/CD pipelines.
- [**Codeberg**](https://codeberg.org) – a privacy-focused Git hosting service powered by [Gitea](https://about.gitea.com). Community-driven and compliant with European data governance standards.

Repositories are created using the **HTTPS protocol** and authenticated with **personal access tokens**.

> 🛡️ Your credentials and tokens are securely stored in the `.env` file and never exposed in plain text.

</details>

---
## 🧾 Project Structure and Usage

This template generates a standardized, reproducible project layout. It separates raw data, code, documentation, setup scripts, and outputs to support collaboration, transparency, and automation.

You can find or update human-readable file descriptions in `file_descriptions.json`.

<details>
<summary>📁 Directory Structure</summary>

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
├── activate.ps1              # PowerShell script to activate the environment
├── deactivate.ps1            # PowerShell script to deactivate the environment
├── bin/                      # Local tools (e.g., rclone binaries, installers)
├── data/                     # Structured project data directory
│   ├── .git/                 # Standalone Git repo for tracking datasets
│   ├── .gitlog               # Git log for the data repository
│   ├── raw/                  # Original, immutable input data
│   ├── interim/              # Intermediate data created during processing
│   └── processed/            # Final, clean data ready for analysis
├── docs/                     # Project documentation, reports, or rendered outputs
├── environment.yml           # Conda-compatible environment definition (Python/R)
├── file_descriptions.json    # JSON file with editable descriptions for all project files
├── requirements.txt          # pip-compatible list of Python dependencies
├── results/                  # Results generated by the project
│   └── figures/              # Charts, plots, and other visual outputs
├── setup/                    # Internal setup module for environment config and CLI tools
│   ├── dependencies.txt      # List of Python dependencies for installation
│   ├── setup.py              # Setup script to register the project as a Python package
│   └── utils/                # Utility functions and scripts for environment setup
└── src/                      # Source code for data processing, analysis, and reporting
    ├── main.*                # Orchestrates the full workflow pipeline
    ├── data_collection.*     # Imports or generates raw data from external sources
    ├── get_dependencies.*    # Checks or retrieves required dependencies
    ├── install_dependencies.*# Installs any missing packages for the environment
    ├── preprocessing.*       # Cleans and transforms raw input data
    ├── modeling.*            # Performs modeling, estimation, or machine learning
    ├── visualization.*       # Creates plots, charts, and visual summaries
    ├── utils.*               # Shared helper functions for reuse across scripts
    ├── environment_setup.*   # (Optional) Initializes the environment (e.g., renv, virtualenv)
    └── workflow.*            # Interactive workflow (e.g., Jupyter notebook or RMarkdown)
```

</details>

> ✳️ Script file extensions (`.py`, `.R`, `.do`, `.m`, `.sas`) are determined by the programming language selected during project setup.

<details>
<summary>🚀 Project Activation</summary>

To configure the project's environment—including project paths, environment variables, and virtual environments—run the activation script for your operating system. These scripts read settings from the `.env` file.

> ⚠️ The `.env` file is excluded from this repository for security reasons.  
> To replicate the environment, follow the instructions in the [Installation](#installation) section.

<details>
<summary>🪟 Windows (PowerShell)</summary>

**Activate:**

```powershell
./activate.ps1
```

**Deactivate:**

```powershell
./deactivate.ps1
```

</details>

<details>
<summary>🐧 macOS / Linux (bash)</summary>

**Activate:**

```bash
source activate.sh
```

**Deactivate:**

```bash
source deactivate.sh
```

</details>

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
| `run-backup`                | Executes a full project backup using preconfigured rules and paths.                               |
| `set-dataset`               | Initializes or registers datasets (e.g., add metadata, sync folders).                            |
| `update-dependencies`       | Retrieves and updates Python and R dependencies listed in `setup/` and `src/`.                   |
| `run-setup` *(in progress)* | Main entry point to initialize or reconfigure the project environment.                           |
| `update-readme`             | Regenerates the `README.md` with updated metadata and file structure.                            |
| `reset-templates`           | Resets or regenerates script templates in `src/` based on project language.                      |
| `code-examples`             | Generates language-specific example code and notebooks (Python, R, SAS, etc.).                   |
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
