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

### 📦 Online (with Git)

```bash
cookiecutter gh:CBS-HPC/replication_package
```

### 📁 Offline (Local Installation)

If Git is not installed, you can still use the template by manually downloading it:

1. Go to [https://github.com/CBS-HPC/replication_package](https://github.com/CBS-HPC/replication_package)
2. Click the green **“Code”** button, then choose **“Download ZIP”**
3. Extract the ZIP file to a location of your choice
4. Then run Cookiecutter with the local path:

```bash
cookiecutter path/to/replication_package
```

> ⚠️ Do **not** use `git clone` if Git is not installed. Manual download is required in this case.

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

This template supports automatic configuration of:

### 📄 License

You can choose from:

- **MIT** – Simple, permissive license
- **BSD-3-Clause** – Permissive with an endorsement clause
- **None** – No license will be included

The selected license will be placed in the root of your generated project as `LICENSE.txt`.

### 🔄 Script Templates

The template generates modular starter scripts in the `src/` directory to support a standardized and reproducible analysis workflow.

Script generation is **language-agnostic**: based on your selected programming language, the template creates script templates with the appropriate file extensions:

- `.py` for Python
- `.R` for R
- `.m` for Matlab
- `.do` for Stata
- `.sas` for SAS

Typical script files include:

- `main.*` – orchestrates the full pipeline
- `data_collection.*` – imports or generates raw data
- `preprocessing.*` – cleans and transforms data
- `modeling.*` – fits models and generates outputs
- `visualization.*` – creates plots and summaries
- `utils.*` – shared helper functions (not directly executable)
- `workflow.ipynb` / `workflow.Rmd` – interactive notebook version of the pipeline

> 📓 The interactive workflow file is:
>
> - `workflow.ipynb` for **Python**, **Stata**, **Matlab**, and **SAS** (Jupyter-compatible kernels)
> - `workflow.Rmd` for **R** (RMarkdown format)

Each script:

- Defines a `main()` function or logical entry point (when applicable)
- Automatically resolves project paths (e.g., `data/raw/`, `results/figures/`)
- Remains passive unless run intentionally, supporting modular and reproducible workflows

> 📂 Scripts are designed for flexibility: run them individually, orchestrate them via `main.*`, or use the notebook/RMarkdown interactively.


### 🧪 Virtual Environment

The template lets you choose how your project's environment is managed. You will be prompted to select one of the following options:

#### **Conda**

- Recommended for projects using both Python and R.
- Allows you to specify the **exact versions** of **Python** and **R** during setup.
- Conda will be **automatically installed** if it is not already available on your system.
- Automatically generates a reproducible `environment.yml` file.
- Ideal for cross-platform workflows, complex dependency resolution, and mixed-language environments.

#### **Venv**

- Uses Python’s built-in `venv` module to create an isolated environment.
- The **Python version will match your system's default Python version** (e.g., Python 3.9.13).
- Dependencies are installed directly into the virtual environment using `pip`.
- Recommended for simple Python-only projects.

#### **Base Installation**

- No new virtual environment is created.
- All dependencies are installed into your system-wide Python environment.
- The **Python version used will depend on your base system installation**.
- Suitable for minimal setups or preconfigured systems.

#### 📦 Environment Files Created (applies to all options)

Regardless of which environment manager you choose, the template will generate the following files to make your project **reproducible and sharable**:

- `environment.yml` – Conda-compatible list of dependencies
- `requirements.txt` – pip-compatible Python package list
- `renv.lock` – (for R projects) snapshot of R package versions using the `renv` package

> ⚠️ **Note:** The template does **not install proprietary software** such as **Stata**, **Matlab**, or **SAS**. If you select one of these languages, you must ensure the corresponding software is installed on your system in advance.

### 🗃️ Version Control

This template supports several version control systems to suit different workflows:

- [**Git**](https://git-scm.com/) (default) – general-purpose version control for code and text files
- [**Datalad**](https://www.datalad.org/) – for data-heavy, file-based versioning; designed to support **FAIR** principles and **Open Science** workflows
- [**DVC**](https://dvc.org/) – for machine learning pipelines, dataset tracking, and model versioning

#### 🛠️ How it works:

- For **Git**, the project root is initialized as a Git repository.
  - The `data/` folder is created as a **separate Git repository**, allowing you to track data independently of source code.
- For **Datalad**, the `data/` folder is initialized as a **Datalad dataset**, enabling advanced data provenance, nesting, and sharing.
- For **DVC**, the `data/` folder is configured for **DVC tracking**, which uses `.dvc` files and external storage to version large data files efficiently.

#### 📄 Auto-generated `.gitignore`

The template includes a `.gitignore` file that automatically excludes:

- `data/` – datasets (raw, interim, processed)
- `bin/` – local binaries like `rclone` and Git annex helpers
- Python build artifacts and virtual environments – e.g., `env/`, `__pycache__/`, `.mypy_cache/`
- Editor/IDE settings – e.g., `.vscode/`, `.idea/`, `.spyproject/`
- Operating system files – e.g., `.DS_Store`, `*.swp`
- Jupyter notebook checkpoints – `.ipynb_checkpoints/`
- Test, log, and coverage files – e.g., `.coverage`, `htmlcov/`, `*.log`

> 🧹 These defaults help keep your repository clean and focused by excluding unnecessary, large, or sensitive files from version control.


### ☁️ Cloud Backup with Rclone

You will be prompted for **email** and **password**  to setup a project backup to the following systems:

- **DeIC Storage** (via SFTP)
- **Dropbox**
- **OneDrive**
- **Local** 
- **Multiple** targets

>  **email** are securely stored in your `.env` file.

### 📡 Remote Repository Platforms

If you choose to publish your project remotely, you will be prompted for your **username**, **privacy settings(private/public)** and **personal access token** to initialize and push the repository using the **HTTPS protocol**:

- **GitHub** (via GitHub CLI)
- **GitLab** (via GitLab CLI)
- **Codeberg**

> 🔐 Your **user credentials** and **personal access tokens** are securely stored in the `.env` file for use in authenticated Git operations.

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
