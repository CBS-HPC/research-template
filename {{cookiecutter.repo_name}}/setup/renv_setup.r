# setup/renv_setup.R

# ----------- Helper Functions ------------

# Safe null operator
`%||%` <- function(x, y) if (!is.null(x)) x else y

# Install and load renv
install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  library(renv)
  message("renv installed and loaded.")
}

# Detect project root based on script file path
get_project_root <- function(file_path = NULL) {
  if (!is.null(file_path)) {
    script_path <- normalizePath(dirname(file_path))
  } else if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    script_path <- normalizePath(dirname(rstudioapi::getActiveDocumentContext()$path))
  } else {
    args <- commandArgs(trailingOnly = FALSE)
    file_arg <- grep("--file=", args, value = TRUE)
    if (length(file_arg) > 0) {
      script_path <- normalizePath(dirname(sub("--file=", "", file_arg)))
    } else {
      script_path <- normalizePath(getwd())
    }
  }
  
  project_root <- normalizePath(file.path(script_path, ".."))
  message(sprintf("Detected project root: %s", project_root))
  return(project_root)
}

# Initialize renv environment
renv_init <- function(file_path = NULL) {
  root <- get_project_root(file_path)
  lockfile_path <- file.path(root, "renv.lock")
  
  if (!file.exists(lockfile_path)) {
    renv::init(bare = TRUE)
    renv::snapshot(lockfile = lockfile_path)
    message("renv initialized and lockfile created at project root.")
  } else {
    message("renv.lock already exists at project root. Initialization skipped.")
  }
}

# Snapshot environment
renv_snapshot <- function(file_path = NULL) {
  root <- get_project_root(file_path)
  lockfile_path <- file.path(root, "renv.lock")
  
  renv::snapshot(lockfile = lockfile_path)
  message("Environment snapshot updated.")
}

# Restore environment
renv_restore <- function(file_path = NULL, check_r_version = TRUE) {
  root <- get_project_root(file_path)
  lockfile_path <- file.path(root, "renv.lock")
  
  if (!file.exists(lockfile_path)) {
    stop("No renv.lock file found at project root. Cannot restore environment.")
  }
  
  if (check_r_version) {
    lockfile <- jsonlite::fromJSON(lockfile_path)
    lock_r_version <- lockfile$R$Version
    current_r_version <- paste(R.version$major, R.version$minor, sep = ".")
    
    if (lock_r_version != current_r_version) {
      warning(sprintf(
        "R version mismatch! Current: %s | Expected: %s",
        current_r_version, lock_r_version
      ))
    } else {
      message("R version matches the lockfile.")
    }
  }
  
  renv::restore(lockfile = lockfile_path)
  message("Environment restored from project root lockfile.")
}

# ----------- Main Script ------------

# Parse file_path argument
args <- commandArgs(trailingOnly = TRUE)
file_path <- NULL

if (length(args) > 0) {
  file_path <- args[1]
  message(sprintf("Input script path received: %s", file_path))
} else {
  message("No file_path argument provided. Falling back to auto-detection.")
}

# Install renv and perform actions
install_renv()
renv_init(file_path)
renv_snapshot(file_path)
# renv_restore(file_path)
