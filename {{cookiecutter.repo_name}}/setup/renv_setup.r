# setup/renv_setup.R

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  library(renv)
  message("renv installed and loaded.")
}

get_project_root <- function() {
  # Assumes this script is inside "setup/" under the project root
  script_path <- normalizePath(dirname(sys.frame(1)$ofile %||% rstudioapi::getActiveDocumentContext()$path))
  project_root <- normalizePath(file.path(script_path, ".."))
  return(project_root)
}

renv_init <- function() {
  root <- get_project_root()
  lockfile_path <- file.path(root, "renv.lock")
  
  if (!file.exists(lockfile_path)) {
    renv::init(bare = TRUE)
    renv::snapshot(lockfile = lockfile_path)
    message("renv initialized and lockfile created at project root.")
  } else {
    message("renv.lock already exists at project root. Initialization skipped.")
  }
}

renv_snapshot <- function() {
  root <- get_project_root()
  lockfile_path <- file.path(root, "renv.lock")
  
  renv::snapshot(lockfile = lockfile_path)
  message("Environment snapshot updated.")
}

renv_restore <- function(check_r_version = TRUE) {
  root <- get_project_root()
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

# ---- Example usage ----

install_renv()
# Uncomment what you want:
renv_init()
renv_snapshot()
# renv_restore()
