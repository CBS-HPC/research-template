from .common import (
    PROJECT_ROOT,
    load_from_env,
    make_safe_path,
    run_script,
)


def lint_r():
    path = PROJECT_ROOT / "R" / "linting.R"
    if not path.exists():
        print(f"ℹ️  Missing: {path}")
        return

    # Call the setup script using the function
    script_path = make_safe_path(str(path), "r")
    cmd = [script_path]
    output = run_script("r", cmd)
    print(output)


def lint_matlab():
    path = PROJECT_ROOT / "src" / "linting.m"
    if not path.exists():
        print(f"ℹ️  Missing: {path}")
        return 
    code_path = make_safe_path(str(path), "matlab")
    cmd = [f"addpath({code_path}); linting"]
    output = run_script("matlab", cmd)
    print(output)


def lint_python():
    path = PROJECT_ROOT / "src" / "linting.py"
    if not path.exists():
        print(f"ℹ️  Missing: {path}")
        return

    # Call the setup script using the function
    script_path = make_safe_path(str(path), "python")
    cmd = [script_path]
    output = run_script("python", cmd)
    print(output)


def main() -> None:
    programming_language = load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter")
    if programming_language.lower() == "python":
        print("Linting python code in './src'")
        lint_python()
    elif programming_language.lower() == "r":
        print("Linting R code in './R'")
        lint_r()
    elif programming_language.lower() == "matlab":
        print("Linting matlab code in './src'")
        lint_matlab()
    else:
        print("not implemented yet")


if __name__ == "__main__":
    main()
