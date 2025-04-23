from utils import *
from code_templates import *
from readme_templates import *

@ensure_correct_kernel
def main():
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    version = load_from_env("VERSION",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION",".cookiecutter")
    email = load_from_env("EMAIL",".cookiecutter")


    # Create scripts and notebook
    create_scripts(programming_language, "./src")
    create_notebooks(programming_language, "./notebooks")
    
    # Create a citation file
    create_citation_file(project_name,version,authors,orcids,version_control,doi=None, release_date=None)

    # Creating README
    creating_readme(repo_name= repo_name, 
                    repo_user = repo_name, 
                    project_name = project_name,
                    project_description = project_description,
                    code_repo = code_repo,
                    programming_language = programming_language,
                    authors = authors,
                    orcids = orcids,
                    emails = email)
                    
    download_README_template(readme_file = "./DCAS template/README.md")


if __name__ == "__main__":
    main()