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

The template guides you through a series of prompts to configure your project. Below is a visual overview of all setup steps:

<details>
<summary>📦 Project Metadata</summary>

This section collects basic project information such as name, author, and description.

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

</details>

<details>
<summary>🧬 Programming Language</summary>

Choose your primary analysis language; for non-Python languages, the path to the software may be required.

```
├── programming_language      → [Python | R | Stata | Matlab | SAS | None]
│   └── If R/Stata/Matlab/SAS selected:
│       └── Prompt for executable path if not auto-detected
```

</details>

<details>
<summary>🧪 Environment Configuration</summary>

Set up virtual environments for Python and/or R using Conda, venv, or your base installation.

```
├── R environment (if R used)
│   └── env_manager_r         → [Conda | Base Installation]
│       ├── If Conda:         → Prompt for R version (e.g., 4.3.2)
│       └── If Base:          → Uses system-installed R
├── Python environment
│   └── env_manager_python    → [Conda | Venv | Base Installation]
│       ├── If Conda:         → Prompt for Python version (e.g., 3.10.12)
│       ├── If Venv:          → Uses current Python kernel version
│       └── If Base:          → Uses system-installed Python
```

</details>

<details>
<summary>🗃️ Version Control</summary>

Select a version control system and configure Git-based tracking for code and optionally for the `data/` directory.

```
├── version_control           → [Git | Datalad | DVC | None]
│   └── If Git:
│       ├── Prompt for Git user.name and user.email
│       ├── Initializes Git repo in project root
│       └── Initializes separate Git repo in `data/` folder
```

</details>

<details>
<summary>☁️ Remote Backup</summary>

Choose where to back up your data: cloud (DeIC, Dropbox, OneDrive), local folders, or multiple options.

```
├── remote_backup             → [DeIC | Dropbox | OneDrive | Local | Multiple | None]
│   ├── DeIC:
│   │   ├── Prompt for CBS email
│   │   └── Prompt for password (stored securely)
│   ├── Dropbox / OneDrive:
│   │   ├── Prompt for email
│   │   └── Prompt for password (stored securely)
│   ├── Local:
│   │   └── Prompt to select a destination path on your machine
│   └── Multiple:
│       └── Allows selection of any combination of the above services
```

</details>

<details>
<summary>📡 Remote Repository Setup</summary>

If you choose to publish the code, the template can automatically create and push to GitHub, GitLab, or Codeberg.

```
├── remote_repo               → [GitHub | GitLab | Codeberg | None]
│   └── If selected:
│       ├── Prompt for platform username
│       ├── Choose visibility: [private | public]
│       └── Enter personal access token (stored in `.env`)
```

</details>

> ⚠️ Proprietary software (e.g., Stata, Matlab, SAS) is **not installed** by the template. You must provide the executable path manually if selected.

---
## 🌐 Remote Setup Support

This template supports automatic configuration of remote versioning, backup, and repository platforms. Click below to expand each section.

<details>
<summary>🗃️ Version Control</summary>

This template supports several version control systems to suit different workflows:

- [**Git**](https://git-scm.com/) (default) – general-purpose version control for code and text files  
- [**Datalad**](https://www.datalad.org/) – for data-heavy, file-based versioning; designed to support **FAIR** principles and **Open Science** workflows  
- [**DVC**](https://dvc.org/) – for machine learning pipelines, dataset tracking, and model versioning

**How it works:**

- For **Git**, the project root is initialized as a Git repository.  
  - The `data/` folder is created as a **separate Git repository**, allowing you to track data independently of source code.  
- For **Datalad**, the `data/` folder is initialized as a **Datalad dataset**, enabling advanced data provenance and modular data management.  
- For **DVC**, the `data/` folder is configured for **DVC tracking**, which uses `.dvc` files and external storage to version large data files.

**Auto-generated `.gitignore` includes:**

- `data/` – raw and processed data folders  
- `bin/` – local binaries  
- Python artifacts – `env/`, `__pycache__/`, `.mypy_cache/`  
- IDE/config files – `.vscode/`, `.idea/`, `.spyproject/`  
- System files – `.DS_Store`, `*.swp`  
- Jupyter checkpoints – `.ipynb_checkpoints/`  
- Logs and test outputs – `.coverage`, `htmlcov/`, `*.log`  

> 🧹 These defaults help keep your repository clean and focused.

</details>

<details>
<summary>☁️ Cloud Backup with Rclone</summary>

You will be prompted for **email** and **password** to set up automatic project backup using `rclone`.

Supported remote systems:

- **DeIC Storage** (via SFTP)  
- **Dropbox**  
- **OneDrive**  
- **Local** storage  
- **Multiple** targets

> 🔐 Your **email** is securely stored in your `.env` file. Passwords are encrypted and not stored in plain text.

</details>

<details>
<summary>📡 Remote Repository Platforms</summary>

If you choose to publish your project remotely, you will be prompted for your:

- **GitHub/GitLab username**
- **Repository visibility** (private/public)
- **Personal access token**

Repositories are pushed using the **HTTPS protocol** and authenticated via tokens.

Supported platforms:

- **GitHub** (via GitHub CLI)  
- **GitLab** (via GitLab CLI)  
- **Codeberg**

> 🔐 Your credentials and tokens are securely saved in the `.env` file for authenticated Git operations.

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
