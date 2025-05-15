# src/renv_setup.R -------------------------------------------------------------

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE))
    install.packages("renv")
  library(renv)
  message("renv installed and loaded.")
}

get_project_root <- function(path = NULL) {
  # --- Helper: Add 'src' if it exists ---
  append_src_if_exists <- function(root) {
    src_path <- file.path(root, "src")
    if (dir.exists(src_path)) {
      return(src_path)
    }
    return(root)
  }
  
  # 1) Explicit path supplied by the caller
  if (!is.null(path)) {
    path <- normalizePath(path, winslash = "/")
    root <- if (file.exists(path) && !dir.exists(path)) dirname(path) else path
    root <- append_src_if_exists(root)
    return(root)
  }
  
  # 2) RStudio active document
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    doc <- rstudioapi::getActiveDocumentContext()$path
    if (nzchar(doc)) {
      root <- dirname(normalizePath(doc, winslash = "/"))
      if (grepl("/src$", root)) {
        return(root)  # Already in src
      }
      root <- append_src_if_exists(root)
      message("Detected project root (RStudio): ", root)
      return(root)
    }
  }
  
  # 3) Command-line runs (R, Rscript, etc.)
  args <- commandArgs(trailingOnly = FALSE)
  
  # Match both --file=script.R and -f script.R
  file_arg <- NULL
  
  # Handle --file=script.R
  long_file <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  
  # Handle -f script.R
  short_idx <- which(args == "-f")
  if (length(short_idx) > 0 && short_idx < length(args)) {
    short_file <- args[short_idx + 1]
  } else {
    short_file <- character(0)
  }
  
  file_arg <- c(long_file, short_file)
  file_arg <- file_arg[nzchar(file_arg)][1]  # Use the first non-empty match
  
  # 4) Fallback - working directory
  if (length(file_arg)) {
    root <- dirname(normalizePath(file_arg, winslash = "/"))
  } else {
    root <- normalizePath(getwd(), winslash = "/")
  }
  
  # Handle /src edge case
  if (!grepl("/src$", root)) {
    root <- append_src_if_exists(root)
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
    renv::install(c("jsonlite", "rmarkdown", "rstudioapi"))
  } else {
    message("renv infrastructure already exists.")
  }
}

safely_snapshot <- function(root_path) {
  tryCatch({
    renv::snapshot(project = root_path, prompt = FALSE)
    message("??? renv.lock written / updated.")
  }, error = function(e) {
    message("?????? Snapshot failed: ", e$message)
  })
}

auto_snapshot <- function(root_path, do_restore = FALSE) {
  ensure_project_loaded(root_path)
  
  lockfile_path <- file.path(root_path, "renv.lock")
  
  if (file.exists(lockfile_path)) {
    message("???? Checking for missing packages ...")
    
    deps <- renv::dependencies(path = root_path)
    used_packages <- unique(deps$Package)
    installed <- rownames(installed.packages(lib.loc = renv::paths$library()))
    #installed <- rownames(installed.packages())
    missing <- setdiff(used_packages, installed)
    
    if (length(missing) > 0) {
      message("???? Installing missing packages: ", paste(missing, collapse = ", "))
      renv::install(missing)
      #install.packages(missing, quiet = TRUE)
    } else {
      message("??? All required packages are already installed.")
    }
    
    if (do_restore) {
      message("???? Restoring lockfile packages ...")
      #renv::restore(project = root_path, prompt = FALSE)
      renv_restore(root_path = root_path,check_r_version = TRUE )
    }
    
  } else {
    message("???? No renv.lock found. Skipping restore.")
  }
  
  message("???? Creating snapshot...")
  safely_snapshot(root_path)
}

renv_restore <- function(root_path, check_r_version = TRUE) {
  ensure_project_loaded(root_path)
  
  lockfile_path <- file.path(root_path, "renv.lock")
  
  if (!file.exists(lockfile_path)) {
    stop("??? Cannot restore: renv.lock file not found at ", lockfile_path)
  }
  
  if (check_r_version) {
    lock <- tryCatch(
      jsonlite::read_json(lockfile_path),
      error = function(e) {
        stop("??? Failed to parse renv.lock: ", e$message)
      }
    )
    
    expect <- lock$R$Version
    have   <- paste(R.version$major, R.version$minor, sep = ".")
    
    if (!identical(expect, have)) {
      warning(sprintf(
        "?????? R version mismatch:\n  - Current:  %s\n  - Expected: %s (from lockfile)", 
        have, expect
      ))
      # If you want to abort instead, replace `warning(...)` with `stop(...)`
    }
  }
  
  renv::restore(project = root_path, prompt = FALSE)
  message("??? Packages restored from lockfile.")
}

# ------------------------------ main -----------------------------------------

args       <- commandArgs(trailingOnly = TRUE)
root_path  <- if (length(args)) args[1] else get_project_root()

install_renv()
renv_init(root_path)      # create renv/ if missing
#renv_snapshot(root_path)  # write renv.lock (non-interactive)
auto_snapshot(root_path, do_restore = FALSE)

