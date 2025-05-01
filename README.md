# 🧪 Cookiecutter Research Replication Template

A fully automated [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/) template for research replication packages. This template sets up a reproducible project structure with support for Python, R, Stata, Matlab, or SAS—along with virtual environments, backup systems, version control, and remote repository setup.

---

## 🧰 Features

✅ Automatically sets up:

- 📁 Standardized project directory with folders for data, code, figures, and documentation
- 🐍 Python virtual environment (`venv`, `conda`, or system)
- 🧬 Programming language scaffolding (Python, R, Stata, Matlab, SAS)
- 🗃️ Version control via Git, Datalad, or DVC
- ☁️ Backup to DeIC, Dropbox, Onedrive, or local with `rclone`
- 📡 Remote repo creation on GitHub, GitLab, or Codeberg
- 🔧 Custom setup scripts and reusable templates for code and documentation
- 💡 Auto-installation of required software and tools (e.g., Git, Rclone, DVC, Datalad) if missing

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

## 🚀 Usage

This template can be used either online (via GitHub) or offline (manually downloaded).

<details>
<summary>📦 Online (with Git)</summary>

Use this option if Git is installed and you want to fetch the template directly from GitHub:

```bash
cookiecutter gh:CBS-HPC/replication_package
```

</details>

<details>
<summary>📁 Offline (Local Installation)</summary>

If Git is **not installed**, you can still use the template by downloading it manually:

1. Go to [https://github.com/CBS-HPC/replication_package](https://github.com/CBS-HPC/replication_package)  
2. Click the green **“Code”** button, then choose **“Download ZIP”**  
3. Extract the ZIP file to a folder of your choice  
4. Run Cookiecutter locally:

```bash
cookiecutter path/to/replication_package
```

> ⚠️ Do **not** use `git clone` if Git is not installed. Manual download is required in this case.

</details>

---

## 🧾 Setup Options

You will be prompted to configure the following options:

| Prompt                     | Description                                 |
| -------------------------- | ------------------------------------------- |
| `project_name`           | Title of your research project              |
| `repo_name`              | Name of the folder and Git repo             |
| `description`            | Short project summary                       |
| `author_name`, `email` | Your name and CBS email                     |
| `orcid`                  | Your ORCID ID                               |
| `version`                | Initial version number (e.g.,`0.0.1`)     |
| `open_source_license`    | MIT, BSD-3-Clause, or None                  |
| `programming_language`   | Python, R, Stata, Matlab, SAS, or None      |
| `version_control`        | Git, Datalad, DVC, or None                  |
| `remote_backup`          | DeIC, Dropbox, Onedrive, Local, or Multiple |
| `env_manager`            | Conda, Venv, or Base installation           |
| `remote_repo`            | GitHub, GitLab, Codeberg, or None           |

The template automatically performs the following:

- Creates the project folder structure
- Generates reusable scripts and module templates in `src/`
- Creates and configures a `.env` file
- Sets up the virtual environment and installs dependencies  
  - If using **Conda**, specific versions of **Python** and **R** can be installed
- Initializes version control and makes an initial commit
- Sets up a Git repository on GitHub, GitLab, or Codeberg (if selected)
- Backs up the project using `rclone` to the selected remote
- Downloads and installs missing open-source tools (e.g., **Git**, **Rclone**, **DVC**, **Datalad**, **Conda**, **GitHub CLI (`gh`)**, **GitLab CLI (`glab`)**) if not already available

> ⚠️ Note: The template **does not install proprietary software** such as **Stata**, **Matlab**, or **SAS**. You must install these separately if selected.


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
