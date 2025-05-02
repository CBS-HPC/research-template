# 🧪 Reproducible Research Template: Structured Workflows and Replication Packages

This project template is designed to help **CBS researchers** create structured, automated, and publication-ready workflows aligned with the principles of **Open Science** and **FAIR** data practices (Findable, Accessible, Interoperable, and Reusable).

Built with [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/), the template supports **Python**, **R**, **Stata**, **Matlab**, and **SAS**, and provides an integrated framework for organizing code, managing datasets, tracking dependencies, enabling version control, and backing up research securely.

Whether you're preparing a replication package for publication, submitting data and code for peer review, or organizing internal research, this tool helps you streamline reproducible research workflows tailored to the needs of the **CBS research community**.

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

```bash
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
## 🗂️ Project Layout

```plaintext
{{cookiecutter.repo_name}}/
├── bin/                  # Tools (e.g., rclone)
├── data/
│   ├── external/         # 3rd-party data
│   ├── interim/          # Intermediate data
│   ├── processed/        # Final, cleaned data
│   └── raw/              # Immutable raw datasets
├── DCAS template/        # Templates for DCAS replication
├── docs/                 # Project documentation
├── results/
│   └── figures/          # Generated figures
├── setup/                # Setup scripts
│   └── utils/            # Utility modules for setup and tools
├── src/                  # Main source code (Python, R, etc.)
├── .env                  # Environment variables
├── .gitignore            # Git ignore rules
├── .rcloneignore         # Ignore rules for backup
├── .treeignore           # Optional for visualization tools
├── CITATION.cff          # Citation metadata
├── LICENSE.txt           # License info
├── README.md             # Project documentation
├── environment.yml       # Conda environment file (if selected)
├── requirements.txt      # Python package list
└── run_setup.sh / .ps1   # One-click project setup
```

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
