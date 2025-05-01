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

---

## 🛠️ Requirements

- Python 3.9+
- `cookiecutter`
- `git`
- Optionally: `conda`, `rclone`, `datalad`, `dvc`, and GitHub CLI (`gh`)

Install Cookiecutter:

```
pip install cookiecutter
```
## 🚀 Usage

Generate a new project using this template:

```
cookiecutter gh:CBS-HPC/replication_package
```
You will be prompted to configure the following options:

| Prompt                    | Description                                     |
|--------------------------|-------------------------------------------------|
| `project_name`           | Title of your research project                  |
| `repo_name`              | Name of the folder and Git repo                 |
| `description`            | Short project summary                           |
| `author_name`, `email`   | Your name and CBS email                         |
| `orcid`                  | Your ORCID ID                                   |
| `version`                | Initial version number (e.g., `0.0.1`)          |
| `open_source_license`    | MIT, BSD-3-Clause, or None                      |
| `programming_language`   | Python, R, Stata, Matlab, SAS, or None          |
| `version_control`        | Git, Datalad, DVC, or None                      |
| `remote_backup`          | DeIC, Dropbox, Onedrive, Local, or Multiple     |
| `env_manager`            | Conda, Venv, or Base installation               |
| `remote_repo`            | GitHub, GitLab, Codeberg, or None               |

The template automatically performs the following:

- Initializes version control and makes an initial commit
- Creates and configures a `.env` file
- Sets up virtual environments and installs dependencies
- Backs up project using `rclone` to selected remote
- Pushes repo to selected remote platform (if configured)
- Creates reusable scripts and module templates for chosen language

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
## 🌐 Remote Setup Support

This template supports automatic configuration of:

### 🗃️ Version Control

- **Git** (default)
- **Datalad** – for data-heavy, file-based versioning
- **DVC** – for ML pipelines and data tracking

### ☁️ Cloud Backup with Rclone

- **DeIC Storage** (via SFTP)
- **Dropbox**
- **OneDrive**
- **Local** or **Multiple** targets

### 📡 Remote Repository Platforms

- **GitHub** (via GitHub CLI)
- **GitLab**
- **Codeberg**

> You will be asked for credentials (e.g., GitHub token or DeIC login) during setup. These are securely stored in your `.env` file and encrypted where applicable.

---

## 🔄 Script Templates

Depending on your selected programming language, the following code templates may be automatically generated in the `src/` directory:

- `main.py`, `preprocessing.py`, `modeling.py`, `visualization.py`
- `workflow.ipynb` – a ready-to-use Jupyter notebook pipeline
- `renv_setup.r` and additional placeholders for R, Stata, Matlab, or SAS

---

## 📄 License

You can choose from:

- **MIT** – Simple, permissive license
- **BSD-3-Clause** – Permissive with an endorsement clause
- **None** – No license will be included

The selected license will be placed in the root of your generated project as `LICENSE.txt`.

---

## 🙏 Acknowledgements

This project was inspired by:

- [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/)
- [FOSTER Open Science](https://www.fosteropenscience.eu/)
- [CBS-HPC Guidelines](https://github.com/CBS-HPC)

Maintained by the **CBS High-Performance Computing (HPC)** team.

---

## 📬 Support

For questions, suggestions, or bug reports:

- Open an [Issue on GitHub](https://github.com/CBS-HPC/replication_package/issues)
- Or contact: [kgp.lib@cbs.dk](mailto:kgp.lib@cbs.dk)

---

*Let us know if you’d like to add badges (e.g., GitHub Actions, license info), screenshots, or links to a demo repository.*
