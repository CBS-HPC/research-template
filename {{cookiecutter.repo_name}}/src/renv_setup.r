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
    renv::install(c("jsonlite", "rmarkdown", "rstudioapi"))
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
  
  if (file.exists(lockfile_path)) {
    # Step 1: Find all declared dependencies
    message("📦 Checking for missing packages ...")
  
    deps <- renv::dependencies(path = folder_path)
    used_packages <- unique(deps$Package)
    installed <- rownames(installed.packages(lib.loc = renv::paths$library()))
    #installed <- rownames(installed.packages())
    missing <- setdiff(used_packages, installed)
    
    # Step 2: Preemptively install missing packages (suppress prompts)
    if (length(missing) > 0) {
      message("📦 Installing missing packages: ", paste(missing, collapse = ", "))
      renv::install(missing)
      #install.packages(missing, quiet = TRUE)
    } else {
      message("✅ All required packages are already installed.")
    }
    
    if (do_restore) {
      message("🕰 Restoring packages from lockfile ...")
      #renv::restore(project = folder_path, prompt = FALSE)
      renv_restore(folder_path = folder_path,check_r_version = TRUE )
    }
    
  } else {
    message("???? No renv.lock found. Skipping restore.")
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

generate_dependencies_file <- function(folder_path, file_name = "dependencies.txt") {
  # List all .R files in the folder and subfolders (use relative paths)
  r_files <- list.files(folder_path, pattern = "\\.R$", full.names = TRUE, recursive = TRUE)
  
  if (length(r_files) == 0) {
    stop("No .R files found in the specified folder or its subfolders.")
  }
  
  # Detect dependencies using renv
  message("Analyzing dependencies in R scripts...")
  dependencies <- renv::dependencies(path = folder_path)
  
  # Extract relevant columns (Package and Version)
  dependency_list <- unique(dependencies[, c("Package", "Version")])
  
  # Fill in missing versions using packageVersion()
  missing_version_idx <- is.na(dependency_list$Version) | dependency_list$Version == ""
  dependency_list$Version[missing_version_idx] <- sapply(
    dependency_list$Package[missing_version_idx],
    function(pkg) {
      if (requireNamespace(pkg, quietly = TRUE)) {
        tryCatch(as.character(packageVersion(pkg)), error = function(e) "Not available")
      } else {
        "Not available"
      }
    }
  )
  
  # Remove unused "Not available" dependencies
  not_available <- dependency_list$Package[dependency_list$Version == "Not available"]
  for (pkg in not_available) {
    pkg_script <- file.path(folder_path, paste0(pkg, ".R"))
    if (!file.exists(pkg_script) || !any(grepl(pkg, basename(r_files)))) {
      message("Removing unused or unreferenced dependency: '", pkg, "'")
      dependency_list <- dependency_list[dependency_list$Package != pkg, ]
    }
  }
  
  # Prepare output path
  output_file <- file.path(folder_path, file_name)
  
  # Metadata
  r_version <- paste(R.version$version.string)
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  relative_r_files <- file.path(".", gsub(paste0(normalizePath(folder_path, winslash = "/"), "/?"), "", normalizePath(r_files, winslash = "/")))
  checked_files <- paste(relative_r_files, collapse = "\n")
  
  # Write header and metadata
  writeLines(
    c(
      "Software version:",
      r_version,
      "",
      paste("Timestamp:", timestamp),
      "",
      "Files checked:",
      checked_files,
      "",
      "Dependencies:"
    ),
    con = output_file
  )
  
  # Append dependency list
  dep_lines <- paste0(dependency_list$Package, ifelse(!is.na(dependency_list$Version) & dependency_list$Version != "", paste0("==", dependency_list$Version), ""))
  write(dep_lines, file = output_file, append = TRUE)
  
  message("'", file_name, "' successfully generated at ", output_file)
}


# ------------------------------ main -----------------------------------------

args       <- commandArgs(trailingOnly = TRUE)
folder_path  <- if (length(args)) args[1] else get_project_root()

install_renv()
renv_init(folder_path)      # create renv/ if missing
#renv_snapshot(folder_path)  # write renv.lock (non-interactive)
auto_snapshot(folder_path, do_restore = FALSE)
generate_dependencies_file(folder_path)
#renv_restore(folder_path, check_r_version = TRUE)