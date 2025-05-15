# src/renv_setup.R -------------------------------------------------------------

`%||%` <- function(x, y) if (!is.null(x)) x else y

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
  file_arg <- sub("^--file=", "", grep("^--file=", args, value = TRUE))
  
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


ensure_project_loaded <- function(folder_path) {
  if (!identical(renv::project(), normalizePath(folder_path))) {
    renv::load(folder_path, quiet = TRUE)
    message("renv project loaded.")
  }
}

renv_init <- function(folder_path) {
  lockfile <- file.path(folder_path, "renv.lock")
  if (!file.exists(lockfile)) {
    renv::init(project = folder_path, bare = TRUE, force = TRUE)
    message("renv infrastructure created.")
  } else {
    message("renv infrastructure already exists.")
  }
}

safely_snapshot <- function(folder_path) {
  tryCatch({
    renv::snapshot(project = folder_path, prompt = FALSE)
    message("??? renv.lock written / updated.")
  }, error = function(e) {
    message("?????? Snapshot failed: ", e$message)
  })
}

auto_snapshot <- function(folder_path, do_restore = FALSE) {
  ensure_project_loaded(folder_path)
  
  lockfile_path <- file.path(folder_path, "renv.lock")
  
  # Step 1: Find all declared dependencies
  message("📦 Checking for missing packages ...")
  deps <- renv::dependencies(path = folder_path, quiet = TRUE)
  used_packages <- unique(deps$Package)
  installed <- rownames(installed.packages())
  missing <- setdiff(used_packages, installed)
  
  # Step 2: Preemptively install missing packages (suppress prompts)
  if (length(missing) > 0) {
    message("📦 Installing missing packages: ", paste(missing, collapse = ", "))
    renv::install(missing)
  } else {
    message("✅ All required packages are already installed.")
  }
  
  # Step 3: Optional restore
  if (do_restore && file.exists(lockfile_path)) {
    message("🕰 Restoring packages from lockfile ...")
    renv_restore(folder_path = folder_path, check_r_version = TRUE)
  } else if (!file.exists(lockfile_path)) {
    message("⚠️ No renv.lock found. Skipping restore.")
  }
  
  # Step 4: Snapshot without prompt
  message("💾 Creating snapshot ...")
  safely_snapshot(folder_path)
}


renv_restore <- function(folder_path, check_r_version = TRUE) {
  ensure_project_loaded(folder_path)
  
  lockfile_path <- file.path(folder_path, "renv.lock")
  
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
  
  renv::restore(project = folder_path, prompt = FALSE)
  message("??? Packages restored from lockfile.")
}

# ------------------------------ main -----------------------------------------

args       <- commandArgs(trailingOnly = TRUE)
folder_path  <- if (length(args)) args[1] else get_project_root()

install_renv()
renv_init(folder_path)      # create renv/ if missing
#renv_snapshot(folder_path)  # write renv.lock (non-interactive)
auto_snapshot(folder_path, do_restore = FALSE)

