



# 🧪 Research Template: Reproducible Workflows and Replication Packages

![Repo size](https://img.shields.io/github/repo-size/CBS-HPC/research-template)
![Last commit](https://img.shields.io/github/last-commit/CBS-HPC/research-template)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC--BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
![Open issues](https://img.shields.io/github/issues/CBS-HPC/research-template)
![Pull requests](https://img.shields.io/github/issues-pr/CBS-HPC/research-template)
![Windows](https://img.shields.io/badge/tested%20on-Windows-blue?logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/tested%20on-Bash%20(Ubuntu)-blue?logo=linux&logoColor=white)


> ⚠️ **Heads up!** This template is still under active development — features, structure, and documentation may evolve as we improve things.

Welcome! This project template is built to help **researchers** create well-organized, automated, and publication-ready workflows that align with **Open Science** and **FAIR** data practices (Findable, Accessible, Interoperable, and Reusable).

Powered by [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/), it supports **Python**, **R**, **Stata**, and **Matlab**, and comes with everything you need to manage code, data, dependencies, version control, and backups — all in one reproducibility-friendly framework.

Whether you're preparing a replication package, submitting code and data for peer review, or just bringing order to an internal project, this tool helps streamline the process.

> ✅ Tested on **Windows (PowerShell)** and **Ubuntu (bash)** environments.

---

🔍 **Key features:**

- 📁 Clear project structure for transparency and consistency  
- 🧬 Multi-language support: Python, R, Stata, and Matlab  
- 🗃️ Built-in version control options: Git, Datalad, or DVC  
- 📦 Auto-generated scripts for analysis, modeling, and visualization  
- 🔐 Environment management via Conda or venv (with UV support)  
- ☁️ Backup integration with DeiC-Storage, Dropbox, and OneDrive  
- 🚀 Remote repository setup for GitHub, GitLab, or Codeberg  
- 🧪 Unit testing support, TDD scaffolds, and CI integration  
- 🧾 Auto-generated metadata files: `README.md`, `LICENSE.txt`, `CITATION.cff`  
- 🧰 Easy activation scripts for both Windows and Bash  
- 📑 Structured documentation of all code, data, and dependencies  
- 📄 Includes support for DCAS-compliant replication packages

---

## 🚀 Getting Started

This section walks you through how to create and configure a new project using the template, either online (with Git) or offline (manual ZIP download), followed by interactive setup options.

### 🛠️ Requirements

- [**Python 3.9+**](https://www.python.org/downloads/) – Required to run the template and environment setup scripts.

- [**cookiecutter**](https://cookiecutter.readthedocs.io/en/latest/) – Used to generate the project structure. 
 > Can be installed by `pip install cookiecutter`.

- [**Git**](https://git-scm.com/downloads) *(Recommended)* 
  > Git is optional for project generation but **required** if using version control or pushing to remote repositories.

- [**Personal Access Token** with proper **permissions**](#-personal-access-tokens-and-permissions) *(Recommended)* 
  > Required to push to **GitHub**, **GitLab**, or **Codeberg**.

- [Stata](https://www.stata.com/) *(if selected)*

- [MATLAB](https://www.mathworks.com/products/matlab.html) *(if selected)*

> If Git or other tools are missing, the template will offer to download and configure them for you.

### 🏗️ Initialize a New Project

To create a new project, run the `cookiecutter` command **from the folder where you want your project directory to be created**. You can use the template either online (with Git) or offline (via manual download).

<details>
<summary><strong>📦 Online (with Git)</strong></summary><br>

Use this option if Git is installed and you want to fetch the template directly from GitHub:

```bash
cookiecutter gh:CBS-HPC/research-template
```

</details>

<details>
<summary><strong>📁 Offline (Local Installation)</strong></summary><br>

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

### 🧩 Interactive Project Configuration

This template guides you through a series of interactive prompts to configure your project:

<details>
<summary><strong>📦 Project Metadata</strong></summary><br>

Provide essential project metadata to support clear documentation, proper attribution, and machine-readable citations.

These details help define your project's identity and improve visibility in collaborative and academic contexts.

```
├── project_name              → Human-readable name
├── repo_name                 → Folder and repository name
├── description               → Short summary of the project
├── author_name               → Your full name
├── email                     → Your email
├── orcid                     → Your ORCID researcher ID
├── version                   → Initial version number (e.g., 0.0.1)
```

This information is used to auto-generate:

- `README.md` – populated with title, description, and author info  
- `CITATION.cff` – for machine-readable academic citation

</details>


<details>
<summary><strong>🔑 License</strong></summary><br>

Clear licensing is essential for open and reproducible research. It defines how others can use, share, and build on your work—whether it's code, data, or documentation.

```
├── code_license              → [MIT | BSD-3-Clause | Apache-2.0 | None]
├── documentation_license     → [CC-BY-4.0 | CC0-1.0 | None]
├── data_license              → [CC-BY-4.0 | CC0-1.0 | None]
```

This information is used to auto-generate:

- `LICENSE.txt` – includes license sections for code, documentation, and data  

> ℹ️ If “None” is selected, the corresponding section will be omitted from the LICENSE file.

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
</details>


<details>
<summary><strong>🧬 Language & Environment</strong></summary><br>

Define the core programming language and set up an isolated environment to ensure your analysis is reproducible across systems and collaborators.

#### ⚙️ Programming Language
Choose your primary scripting language. The template supports multi-language projects and automatically generates a modular codebase tailored to your selection.

```
├── programming_language      → [Python | R | Stata | Matlab | None]
│   └── If R/Stata/Matlab selected:
│       └── Prompt for executable path if not auto-detected
```

📝 Based on your selected language, the template will automatically generate example scripts and notebooks for each stage of the workflow — see [How it works](#-how-it-works) for details.

#### 🧪 Environment Configuration

To ensure reproducibility in computational research, it’s essential to isolate your project’s software dependencies.

Virtual environments allow you to lock in specific package versions and avoid conflicts with system-wide tools or other projects. This makes it possible for collaborators—and future you—to re-run analyses under the exact same conditions.

Set up isolated virtual environments using **Conda**, **UV (venv backend)**, or **system installation**.

```
├── Python environment
│   └── env_manager_python        → [Conda | UV]
│       ├── If Conda:             → Prompts for Python version
│       ├── If UV (venv backend): → Uses current Python kernel version
│                                 → Creates a `.venv` directory for the environment
│                                 → Initializes a UV project and generates `uv.lock` to capture dependencies
├── R environment (if R used)
│   └── env_manager_r             → [Conda | System R]
│       ├── If Conda:             → Prompts for R version
│       └── If System R:          → Searches system PATH for installed R
│                                 → Prompts for path if not found
│       → In all cases:           → Initializes an isolated R environment using `renv` in the `/R` directory
│                                 → Generates `renv.lock` to capture R package versions
├── Proprietary software (if selected)
│   └── [Stata | Matlab]
│       ├── Searches system PATH for installed application
│       └── Prompts user for executable path if not found
```

**Environment manager options:**

- [**Conda**](https://docs.conda.io/en/latest/) – A widely used environment and package manager for both Python and R. Supports precise version control, reproducibility, and cross-platform compatibility.  
- [**UV**](https://github.com/astral-sh/uv) – A fast, modern Python package manager and `venv` backend. Provides isolated environments and accelerated dependency resolution. Ideal for Python-only workflows.  
- [**renv**](https://rstudio.github.io/renv/) – An R package for creating isolated, project-local environments. Captures exact package versions in a `renv.lock` file, enabling reproducibility similar to `requirements.txt` or `environment.yml`.

Regardless of your choice, the following files are generated to document your environment:

- `environment.yml` – Conda-compatible list of dependencies  
- `requirements.txt` – pip-compatible Python package list  
- `renv.lock` – (if R is selected) snapshot of R packages using the `renv` package
- `uv.lock` – (if Venv is selected) snapshot of python packages using the `uv` package manager  

⚠️ When using **UV** or **Pre-Installed R**, the `environment.yml` file is created **without Conda's native environment tracking**. As a result, it may be **less accurate or reproducible** than environments created with Conda.

⚠️ If proprietary software (e.g., Stata, Matlab) is selected, the system will first **search your PATH**. If not found, you’ll be prompted to manually enter the executable path.  

💡 Conda will be downloaded and installed automatically if it's not already available.

</details>

<details>
<summary><strong>🗃️ Version Control</strong></summary><br>

Version control is a cornerstone of reproducible research.It enables you to track changes to your code, data, and analysis pipelines over time—ensuring transparency, accountability, and collaboration.

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

#### 🔧 How it works:

- **Git**: initializes the project root as a Git repository  
  - Also creates a separate Git repo in `data/` to track datasets independently  
- **Datalad**: builds on Git by creating a [Datalad dataset](https://handbook.datalad.org/en/latest/basics/101-137-datasets.html) in `data/`  
- **DVC**: runs `dvc init` and sets up `data/` as a [DVC-tracked directory](https://dvc.org/doc/start/data-management) using external storage and `.dvc` files

#### 📝 Auto-generated `.gitignore` includes:

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
<summary><strong>☁️ Backup with Rclone</strong></summary><br>

Data loss can compromise months or years of research. To support **reproducible**, **secure**, and **policy-compliant** workflows, this template offers automated backup to CBS-approved storage providers using [`rclone`](https://rclone.org). Whether working locally or in the cloud, your data can be reliably mirrored to trusted storage systems.

```
├── remote_backup             → [DeIC | Dropbox | OneDrive | Local | Multiple | None]
│   ├── DeIC:
│   │   ├── Prompt for email
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

- [**DeIC-Storage**](https://storage.deic.dk/) – configured via **SFTP with password and MFA** (see instructions under “Setup → SFTP”)  
- [**Dropbox**](https://www.dropbox.com/)  
- [**OneDrive**](https://onedrive.live.com/)  
- **Local** storage – backup to a folder on your own system  
- **Multiple** – select any combination of the above

> 🔐 All credentials are stored in `rclone.conf`.  
> ☁️ `rclone` is automatically downloaded and installed if not already available on your system.

</details>

<details>
<summary><strong>📡 Remote Repository Setup</strong></summary><br>

Publishing your project to a remote Git hosting platform is a key step toward transparent, collaborative, and **reproducible** research.

A remote repository provides versioned backups, collaboration support, and integration with tools like CI pipelines—crucial for reproducible and FAIR research.

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

Repositories are created using the **HTTPS API**, and authenticated with [**personal access tokens**](#-personal-access-tokens-and-permissions).

> 🛡️ Your credentials and tokens are securely stored in the `.env` file and never exposed in plain text.

#### 🔐 Personal Access Tokens and Permissions

A Personal Access Token (PAT) is needed to:

- Create remote repositories
- Push CI configuration files
- Enable automated workflows (e.g. GitHub Actions, GitLab CI)

##### 🔎 Required Token Scopes by Platform

| Platform   | Purpose                              | Required Scopes           |
|------------|--------------------------------------|---------------------------|
| **GitHub** | Create repos, push code, configure CI workflows | `repo`, `workflow`       |
| **GitLab** | Create repos, push code, configure CI/CD        | `api`                    |
| **Codeberg** | Create repo (CI enabled manually)  | `repo` *(if using API)*   |


</details>

---
## 🧾 How It Works: Structure & Scripts

This template generates a standardized, reproducible project layout. It separates raw data, code, documentation, setup scripts, and outputs to support collaboration, transparency, and automation.


<details>
<summary><strong>🚀 Project Activation</strong></summary><br>

To configure the project's environment—including project paths, environment variables, and virtual environments—run the activation script for your operating system. These scripts read settings from the `.env` file.

#### 🪟 Windows (PowerShell)

```powershell
#Activate
./activate.ps1

#Deactivate
./deactivate.ps1
```

#### 🐧 macOS / Linux (bash)

```bash
#Activate
source activate.sh

#Deactivate
source deactivate.sh
```

</details>

<details>
<summary><strong>🔧 CLI Tools</strong></summary><br>

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

#### 🛠️ Usage

After activating your environment, run commands like:

```bash
run-setup
set-dataset
update-requirements
```

</details>

<details>
<summary><strong>🗂️ Configuration Files (Root-Level)</strong></summary><br>

The following configuration files are intentionally placed at the root of the repository. These are used by various tools for environment setup, dependency management, templating, and reproducibility.

| File              | Purpose                                                                                          |
|-------------------|--------------------------------------------------------------------------------------------------|
| `pyproject.toml`  | Project metadata for packaging, CLI tools, sync rules, platform logic, and documentation         |
| `.env`            | Defines environment-specific variables (e.g., paths, secrets). Typically excluded from version control. |
| `.gitignore`      | Excludes unnecessary files from Git version control                                              |
| `environment.yml` | Conda environment definition for Python/R, including packages and versions                       |
| `requirements.txt`| Pip-based Python dependencies for lightweight environments                                       |
| `renv.lock`       | Records the exact versions of R packages used in the project                                    |
| `uv.lock`         | Locked Python dependencies file for reproducible installs with `uv`                            |

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

</details>

<details>
<summary><strong>🛠️ Script Templates</strong></summary><br>

This template helps you organize your scripts in a standardized way across programming languages—making it easier to rerun analyses, share with collaborators, and automate complex workflows over time.

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
<summary><strong>🧪 Unit Testing</strong></summary><br>

Unit tests play a critical role in **ensuring the reliability and reproducibility** of your research code. This template provides built-in testing support for **Python**, **R**, **MATLAB**, and **Stata** to help you catch errors early and build trust in your results.

It supports both:

- **Traditional unit testing** – write tests to validate existing code
- **Test-Driven Development (TDD)** – write tests before code to guide design

> 🧪 Test scaffolding is automatically generated for each core analysis script (e.g., `s00_main`, `s04_preprocessing`), making it easy to integrate testing from day one.

---

### 📁 File Structure & Test Execution

During setup, a dedicated `tests/` folder is created. Matching test files are generated for each language and script:

| Language | Test Framework     | Code Folder     | Test Folder         | File Format     | Run Command                                                   |
|----------|--------------------|------------------|----------------------|------------------|----------------------------------------------------------------|
| Python   | `pytest`           | `src/`           | `tests/`             | `test_*.py`      | `pytest`                                                       |
| R        | `testthat`         | `R/`             | `tests/testthat/`    | `test-*.R`       | `testthat::test_dir("tests/testthat")`<br>`Rscript -e '...'`   |
| MATLAB   | `matlab.unittest`  | `src/`           | `tests/`             | `test_*.m`       | `runtests('tests')`<br>`matlab -batch "..."`                   |
| Stata    | `.do` script-based | `stata/do/`      | `tests/`             | `test_*.do`      | `do tests/test_s00_main.do`<br>`stata -b do tests/...`         |

📄 Example (Python):

```
# Matching tests
src/s00_main.py
tests/test_s00_main.py

# Run Tests
pytest
```

💡 See the [CI section](#-continuous-integration-ci) for more on automated test execution.

---

### ✅ Best Practices

- **Test core logic and workflows** – e.g., cleaning, transformation, modeling functions  
- **Cover edge cases** – missing data, invalid inputs, unexpected file formats  
- **Write independent tests** – avoid shared state between tests  
- **Use language-specific assertions:**
  - Python: `assert`
  - R: `expect_equal()`, `expect_error()`
  - MATLAB: `verifyEqual()`, `verifyTrue()`
  - Stata: `assert`

🧩 Match test names to your scripts for clarity:  
Example: `s05_modeling.R` → `test-s05_modeling.R`

> ✅ Your tests don’t have to be exhaustive. Focus on **critical functions** and **key workflow branches**.

</details>

<details>
<summary><strong>⚙️ Continuous Integration (CI)</strong></summary><br>

Continuous Integration (CI) helps ensure your research project is **reproducible, portable, and robust** across different systems. This template includes built-in CI support for **Python**, **R**, and **MATLAB** using:

- **GitHub Actions**
- **GitLab CI/CD**
- **Codeberg CI** (Woodpecker)

✅ Even without writing **unit tests**, the default CI configuration will still verify that your project environment installs correctly across platforms (e.g., Linux, Windows, macOS).This provides early detection of broken dependencies, incompatible packages, or missing setup steps — critical for collaboration and long-term reproducibility.

#### 🔁 What the CI Pipeline Does

Each auto-generated CI pipeline:

1. Installs the appropriate language runtime (e.g., Python, R, MATLAB)
2. Installs project dependencies:
   - Python: via `requirements.txt`
   - R: via `renv::restore()` using `R/renv.lock`
3. Executes tests in the `tests/` directory (if present)
4. Outputs logs and results for debugging or documentation

#### ✅ Supported CI Platforms

| Platform     | Supported Languages     | OS Support              | Config File                |
|--------------|--------------------------|--------------------------|----------------------------|
| **GitHub**   | Python, R, MATLAB        | Linux, Windows, macOS    | `.github/workflows/ci.yml` |
| **GitLab**   | Python, R, MATLAB        | Linux only               | `.gitlab-ci.yml`           |
| **Codeberg** | Python, R *(no MATLAB)*  | Linux only               | `.woodpecker.yml`          |

> ⚠️ **Stata is not supported** on any CI platform due to licensing limitations and lack of headless automation.

#### ⚠️ MATLAB CI Caveats

MATLAB CI support is included as a **starter configuration**. It may require manual setup, including licensing and tokens.

- **GitHub Actions**: Uses [`setup-matlab`](https://github.com/matlab-actions/setup-matlab) and requires a `MATLAB_TOKEN`.
- **GitLab CI/CD**: Uses [MathWorks' CI template](https://github.com/mathworks/matlab-gitlab-ci-template) and requires a license server or `MLM_LICENSE_FILE`.

#### 📝 Codeberg CI Requires Activation

CI is **not enabled by default** on Codeberg. To enable:

- Submit a request via [Codeberg CI Activation Form](https://codeberg.org/Codeberg-e.V./requests/issues/new?template=ISSUE_TEMPLATE%2fWoodpecker-CI.yaml)
- Learn more in the [Codeberg CI documentation](https://docs.codeberg.org/ci/)

#### 🛠️ CI Control via CLI

You can toggle CI setup on or off at any time using the built-in CLI:

```bash
ci-control --on
ci-control --off
```

##### 🧷 Skip CI for a Commit

Use this Git alias to skip CI on minor commits:

```
git commit-skip "Updated documentation"
```

</details>

<details>
<summary><strong>📁 Directory Structure</strong></summary><br>

This template uses a modular folder layout that promotes transparency, reproducibility, and clear separation of data, code, results, and documentation—making your project easy to navigate and maintain.

📝 File and folder descriptions are stored in `pyproject.toml` under `[tool.research_template.file_descriptions]`. See the [Configuration Files section](#-configuration-files-root-level) for details.

#### 🗂️ Top-Level Overview

```
├── .git/                     # Git repository metadata
├── .gitignore                # Files/folders excluded from Git tracking
├── .github/                 # GitHub Actions workflows for CI/CD
├── .venv/                   # Local Python virtual environment
├── .conda/                  # Local Conda environment (Python/R)
├── LICENSE.txt              # License for code, data, and documentation
├── CITATION.cff             # Citation metadata for scholarly reference
├── README.md                # Main README with project usage and structure
├── pyproject.toml           # Project metadata and CLI configuration
├── activate.* / deactivate.* # Environment activation scripts (.ps1/.sh)
├── environment.yml          # Conda environment definition
├── requirements.txt         # pip-compatible Python dependency list
├── renv.lock                # R package lock file created by renv
├── uv.lock                # R package lock file created by renv

```

> 🔁 `activate.*` and `deactivate.*` are either PowerShell (`.ps1`) or Bash (`.sh`) scripts, depending on your platform (Windows or macOS/Linux).

#### 📦 Project Subdirectories

```
├── bin/                     # Executables and helper tools (e.g., rclone)
├── data/
│   ├── .git/                # Git repo for tracking datasets
│   ├── .gitlog              # Git commit log specific to datasets
│   ├── 00_raw/              # Original, immutable input data
│   ├── 01_interim/          # Cleaned/transformed intermediate data
│   ├── 02_processed/        # Final, analysis-ready datasets
│   └── 03_external/         # Data from third-party sources
├── docs/                    # Documentation, reports, or rendered output
├── results/
│   └── figures/             # Visual outputs (charts, plots, etc.)
```

#### 🔧 Setup & Configuration

```
├── setup/
│   ├── setup.py             # Registers setup package
│   ├── pyproject.toml       # CLI tool registration and config
│   ├── dependencies.txt     # Setup-specific Python dependencies
│   └── utils/               # Utility scripts for setup and automation
```

#### 🧬 Source Code

```
└── src (R/stata)/
    ├── dependencies.txt            # src-level dependency list
    ├── get_dependencies.*          # Dependency installation logic
    ├── s00_main.*                  # Full workflow orchestration
    ├── s00_workflow.*              # Notebook-based pipeline
    ├── s01_install_dependencies.*  # Project package installer
    ├── s02_utils.*                 # Shared helper functions
    ├── s03_data_collection.*       # Data import/generation logic
    ├── s04_preprocessing.*         # Data cleaning and transformation
    ├── s05_modeling.*              # Statistical modeling and ML
    └── s06_visualization.*         # Plotting and summaries
```

> ✳️ Script extensions (`.py`, `.R`, `.do`, `.m`) depend on the language selected during project setup.

#### 🧪 Unit Tests

```
├── tests/
│   ├── test_get_dependencies.*           # Tests dependency resolution
│   ├── test_s00_main.*                   # Tests pipeline orchestration
│   ├── test_s01_install_dependencies.*   # Tests installation logic
│   ├── test_s02_utils.*                  # Tests utility functions
│   ├── test_s03_data_collection.*        # Tests data handling
│   ├── test_s04_preprocessing.*          # Tests data cleaning
│   ├── test_s05_modeling.*               # Tests modeling logic
│   └── test_s06_visualization.*          # Tests plotting and outputs
```

> ✳️ Script extensions (`.py`, `.R`, `.do`, `.m`) depend on the language selected during project setup.
</details>

<details>
<summary><strong>📚 DCAS Compatibility</strong></summary><br>

This template is designed to support the creation of replication packages that are fully compatible with the [Data and Code Availability Standard (DCAS)](https://datacodestandard.org/), a widely endorsed initiative to promote transparency and reproducibility in social science research.

By structuring code, data, metadata, and documentation into clear, well-separated folders—with standard naming conventions, licensing, and README scaffolds—the template helps you align with the expectations of journals that require or recommend DCAS compliance.

Key features that support DCAS alignment:

- 📂 Separation of raw, interim, and processed data
- 📜 Auto-generated licensing and citation metadata (`LICENSE.txt`, `CITATION.cff`)
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
