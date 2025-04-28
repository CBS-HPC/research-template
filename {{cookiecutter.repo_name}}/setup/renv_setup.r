# setup/renv_setup.R

# Helper for safe NULL handling
`%||%` <- function(x, y) if (!is.null(x)) x else y

# Install and load renv
install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  library(renv)
  message("renv installed and loaded.")
}

# Find the project root one folder up from the script location
get_project_root <- function() {
  # Check if RStudio is running
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    # RStudio session: get active document path
    script_path <- normalizePath(dirname(rstudioapi::getActiveDocumentContext()$path))
  } else {
    # Non-RStudio session (e.g., running from terminal or Python)
    script_path <- normalizePath(dirname(sys.frames()[[1]]$ofile))
  }
  project_root <- normalizePath(file.path(script_path, ".."))
  return(project_root)
}

# Initialize renv environment
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

# Snapshot environment state
renv_snapshot <- function() {
  root <- get_project_root()
  lockfile_path <- file.path(root, "renv.lock")
  
  renv::snapshot(lockfile = lockfile_path)
  message("Environment snapshot updated.")
}

# Restore environment from lockfile
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
renv_init()
renv_snapshot()
# renv_restore()
