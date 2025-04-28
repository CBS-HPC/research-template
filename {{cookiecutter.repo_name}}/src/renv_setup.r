# renv_setup.R

install_renv <- function() {
  if (!requireNamespace("renv", quietly = TRUE)) {
    install.packages("renv")
  }
  library(renv)
  message("renv installed and loaded.")
}

renv_init <- function() {
  if (!file.exists("renv.lock")) {
    renv::init()
    message("renv initialized.")
  } else {
    message("renv.lock already exists. Initialization skipped.")
  }
}

renv_snapshot <- function() {
  renv::snapshot()
  message("Environment snapshot created.")
}

renv_restore <- function(check_r_version = TRUE) {
  if (!file.exists("renv.lock")) {
    stop("No renv.lock file found. Cannot restore environment.")
  }
  
  if (check_r_version) {
    lockfile <- jsonlite::fromJSON("renv.lock")
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
  
  renv::restore()
  message("Environment restored.")
}

# ---- Example usage ----

install_renv()
# Uncomment the actions you want:
# renv_init()
# renv_snapshot()
# renv_restore()
