# src/renv_setup.R -------------------------------------------------------------

`%||%` <- function(x, y) if (!is.null(x)) x else y

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE))
    install.packages("renv")
  library(renv)
  message("renv installed and loaded.")
}

get_project_root <- function(path = NULL) {
  # 1) Explicit path supplied by the caller
  if (!is.null(path)) {
    path <- normalizePath(path, winslash = "/")
    root <- if (file.exists(path) && !dir.exists(path)) dirname(path) else path
    return(root)
  }
  
  # 2) RStudio active document
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    doc <- rstudioapi::getActiveDocumentContext()$path
    if (nzchar(doc)) {
      root <- dirname(normalizePath(doc, winslash = "/"))
      
      # Check if the root is inside 'src' and adjust accordingly
      if (grepl("/src$", root)) {
        root <- dirname(root)  # Move one level up from 'src'
      }
      
      message("Detected project root (RStudio): ", root)
      return(root)
    }
  }
  
  # 3) Command-line runs (R, Rscript, etc.)
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  
  # 4) Fallback - working directory
  if (length(file_arg)) {
    root <- dirname(normalizePath(file_arg, winslash = "/"))
  } else {
    root <- normalizePath(getwd(), winslash = "/")
  }
  
  # Adjust if the root is inside 'src'
  if (grepl("/src$", root)) {
    root <- dirname(root)  # Move one level up from 'src'
  }
  
  message("Detected project root: ", root)
  return(root)
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

auto_snapshot <- function(root_path) {
  ensure_project_loaded(root_path)
  
  # Check if renv.lock exists
  lockfile_path <- file.path(root_path, "renv.lock")
  
  if (file.exists(lockfile_path)) {
    # If the lockfile exists, check if there are missing packages
    message("???? Checking for missing packages ...")
    
    deps <- renv::dependencies(path = root_path)
    used_packages <- unique(deps$Package)
    installed <- rownames(installed.packages())
    missing <- setdiff(used_packages, installed)
    
    if (length(missing) > 0) {
      # Install the missing packages
      message("???? Installing missing packages: ", paste(missing, collapse = ", "))
      install.packages(missing, quiet = TRUE)
    } else {
      message("??? All required packages are already installed.")
    }
    
  } else {
    message("No renv.lock found. Skipping restore.")
  }
  
  # Snapshot the environment to update renv.lock
  message("???? Creating snapshot...")
  renv::snapshot(project = root_path, prompt = FALSE)
  message("??? renv.lock written / updated.")
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
#renv_snapshot(root_path)  # write renv.lock (non-interactive)
auto_snapshot(root_path)
# renv_restore(root_path) # uncomment when you actually want to restore
