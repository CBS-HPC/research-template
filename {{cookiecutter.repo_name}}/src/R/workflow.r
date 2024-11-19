source('data_collection.R')
source('preprocessing.R')
source('modeling.R')
source('utils.R')
source('visualization.R')

run_workflow <- function() {
  run_data_collection()
  run_preprocessing()
  run_modeling()
  run_utils()
  run_visualization()
}

run_workflow()