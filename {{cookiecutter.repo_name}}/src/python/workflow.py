
# Import the step scripts
import data_collection
import preprocessing
import modeling
import utils
import visualization

def run_workflow():
    data_collection.run_data_collection()
    preprocessing.run_preprocessing()
    modeling.run_modeling()
    utils.run_utils()
    visualization.run_visualization()

if __name__ == "__main__":
    run_workflow()