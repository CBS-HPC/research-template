# src/renv_setup.R -------------------------------------------------------------

`%||%` <- function(x, y) if (!is.null(x)) x else y

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE))
    install.packages("renv")
  library(renv)
  message("renv installed and loaded.")
}

get_project_root <- function(path = NULL) {
  if (!is.null(path)) {
    root <- normalizePath(dirname(path))
  } else {
    root <-  getwd()
  }
  message("Detected project root: ", root)
  root
}

ensure_project_loaded <- function(root_path) {
  if (!identical(renv::project(), normalizePath(root_path))) {
    renv::load(root_path, quiet = TRUE)
    message("renv project loaded.")
  }
}

renv_init <- function(root_path) {
  lockfile <- file.path(root_path, "renv.lock")
  if (!file.exists(lockfile)) {
    renv::init(project = root_path, bare = TRUE, force = TRUE)
    message("renv infrastructure created.")
  } else {
    message("renv infrastructure already exists.")
  }
}

renv_snapshot <- function(root_path) {
  ensure_project_loaded(root_path)
  renv::snapshot(project = root_path, prompt = FALSE)
  message("renv.lock written / updated.")
}

renv_restore <- function(root_path, check_r_version = TRUE) {
  ensure_project_loaded(root_path)
  
  if (check_r_version) {
    lock <- jsonlite::read_json(file.path(root_path, "renv.lock"))
    expect <- lock$R$Version
    have   <- paste(R.version$major, R.version$minor, sep = ".")
    if (expect != have)
      warning("R version mismatch: current ", have, " – lockfile ", expect)
  }
  
  renv::restore(project = root_path, prompt = FALSE)
  message("Packages restored from lockfile.")
}

# ------------------------------ main -----------------------------------------

args       <- commandArgs(trailingOnly = TRUE)
root_path  <- if (length(args)) args[1] else get_project_root()

install_renv()
renv_init(root_path)      # create renv/ if missing
renv_snapshot(root_path)  # write renv.lock (non-interactive)
# renv_restore(root_path) # uncomment when you actually want to restore
