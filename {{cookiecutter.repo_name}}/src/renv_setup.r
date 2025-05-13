# src/renv_setup.R -------------------------------------------------------------

`%||%` <- function(x, y) if (!is.null(x)) x else y

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE))
    install.packages("renv")
  library(renv)
  message("renv installed and loaded.")
}

get_project_root <- function(path = NULL) {
  # ------------------------------------------------------------------
  # 1) If a path was supplied, trust it. It can be either a file or dir
  # ------------------------------------------------------------------
  if (!is.null(path)) {
    path <- normalizePath(path, winslash = "/")
    root <- if (file.exists(path) && !dir.exists(path))
      dirname(path) else path       # file  -> its directory
    return(root)
  }
  
  # ------------------------------------------------------------------
  # 2) Try RStudio active document
  # ------------------------------------------------------------------
  if (requireNamespace("rstudioapi", quietly = TRUE) &&
      rstudioapi::isAvailable()) {
    doc <- rstudioapi::getActiveDocumentContext()$path
    if (nzchar(doc)) {
      root <- dirname(normalizePath(doc, winslash = "/"))
      message("Detected project root (RStudio): ", root)
      return(root)
    }
  }
  
  # ------------------------------------------------------------------
  # 3) Try command-line invocations  (--file=  or  -f <file>)
  # ------------------------------------------------------------------
  args <- commandArgs(trailingOnly = FALSE)
  
  # --file=/path/to/script.R
  file_arg <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  
  # -f /path/to/script.R
  if (!length(file_arg)) {
    idx <- which(args == "-f")
    if (length(idx) && idx < length(args))
      file_arg <- args[idx + 1]
  }
  
  if (length(file_arg) && nzchar(file_arg)) {
    root <- dirname(normalizePath(file_arg, winslash = "/"))
    message("Detected project root (CLI): ", root)
    return(root)
  }
  
  # ------------------------------------------------------------------
  # 4) Fallback – use the working directory
  # ------------------------------------------------------------------
  root <- normalizePath(getwd(), winslash = "/")
  message("Fallback project root: ", root)
  root
}

get_project_root_backup <- function(path = NULL) {
    if (!is.null(path)) {
      root <- normalizePath(path)
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
