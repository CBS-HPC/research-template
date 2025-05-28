import os
import pathlib
from textwrap import dedent

from .general_tools import *
from .code_templates import write_script
from .readme_templates import main as update_readme_main
from .get_dependencies import main as get_setup_dependencies_main

package_installer(required_libraries=['nbformat'])
#package_installer(required_libraries=['rpds-py==0.21.0', 'nbformat'])

def create_example(project_language, folder_path):
    """
    Create a realistic example project for a specified programming language.
    
    Args:
        project_language (str): "r", "python", "stata", "matlab", "sas"
        folder_path (str): Where to create the project
    """
    if project_language.lower() not in ["r", "python", "stata", "matlab", "sas"]:
        raise ValueError("Supported languages: r, python, stata, matlab, sas")

    if project_language.lower() == "r":
        create_r_example(folder_path)
    elif project_language.lower() == "python":
        create_python_example(folder_path)
    elif project_language.lower() == "stata":
        create_stata_example(folder_path)
    elif project_language.lower() == "matlab":
        create_matlab_example(folder_path)
    elif project_language.lower() == "sas":
        create_sas_example(folder_path)


### === LANGUAGE EXAMPLE CREATORS === ###

def create_r_example(folder_path):
    scripts = {
        "s03_data_collection": dedent("""
            s03_data_collection <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              raw_data <- file.path(base_path, "data", "00_raw")
              interim_data <- file.path(base_path, "data", "01_interim")
              processed_data <- file.path(base_path, "data", "02_processed")
              
              collect_data <- function() {
                data <- mtcars
                if (!dir.exists(raw_data)) dir.create(raw_data, recursive = TRUE)
                saveRDS(data, file.path(raw_data, "mtcars_raw.rds"))
                return(data)
              }
              
              main <- function() {
                print("Running data_collection...")
                collect_data()
              }
              
              main()
            })
        """),
        "s04_preprocessing": dedent("""
            s04_preprocessing <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              raw_data <- file.path(base_path, "data", "00_raw")
              interim_data <- file.path(base_path, "data", "01_interim")
              processed_data <- file.path(base_path, "data", "02_processed")
              
              library(dplyr)
              
              preprocess_data <- function(data) {
                data <- data %>% mutate(mpg_z = scale(mpg))
                if (!dir.exists(interim_data)) dir.create(interim_data, recursive = TRUE)
                saveRDS(data, file.path(interim_data, "mtcars_interim.rds"))
                return(data)
              }
              
              main <- function() {
                print("Running preprocessing...")
                data <- readRDS(file.path(raw_data, "mtcars_raw.rds"))
                preprocess_data(data)
              }
              
              main()
            })
        """),
        "s05_modeling": dedent("""
            s05_modeling <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              interim_data <- file.path(base_path, "data", "01_interim")
              processed_data <- file.path(base_path, "data", "02_processed")
              
              build_model <- function(data) {
                model <- lm(mpg ~ wt + hp, data = data)
                if (!dir.exists(processed_data)) dir.create(processed_data, recursive = TRUE)
                saveRDS(model, file.path(processed_data, "mtcars_model.rds"))
                return(model)
              }
              
              main <- function() {
                print("Running modeling...")
                data <- readRDS(file.path(interim_data, "mtcars_interim.rds"))
                build_model(data)
              }
   
              main()
            })
        """),
        "s06_visualization": dedent("""
            s06_visualization <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              interim_data <- file.path(base_path, "data", "01_interim")
              processed_data <- file.path(base_path, "data", "02_processed")
              figures_path <- file.path(base_path, "results", "figures")
              
              library(ggplot2)
              
              visualize_model <- function(data, model) {
                data <- data %>% mutate(predicted = predict(model, newdata = data))
                plot <- ggplot(data, aes(x = mpg, y = predicted)) +
                  geom_point() +
                  geom_smooth(method = "lm", se = FALSE) +
                  labs(title = "Actual vs Predicted MPG")
                if (!dir.exists(figures_path)) dir.create(figures_path, recursive = TRUE)
                ggsave(file.path(figures_path, "actual_vs_predicted_mpg.png"), plot)
              }
              
              main <- function() {
                print("Running visualization...")
                data <- readRDS(file.path(interim_data, "mtcars_interim.rds"))
                model <- readRDS(file.path(processed_data, "mtcars_model.rds"))
                visualize_model(data, model)
              }
              
              main()  
            })
        """)
    }
    
    for name, content in scripts.items():
        write_script(folder_path, name, ".R", content)
    
    main_content = dedent("""
        # Main runner
        
        #source('s01_install_dependencies.R')
        source('s03_data_collection.R')
        source('s04_preprocessing.R')
        source('s05_modeling.R')
        source('s06_visualization.R')

        s03_data_collection$main()
        s04_preprocessing$main()
        s05_modeling$main()
        s06_visualization$main()
        print("done")
    """)
    write_script(folder_path, "s00_main", ".R", main_content)

def create_python_example(folder_path):
    scripts = {
        "s03_data_collection": dedent("""
            import os, pickle

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            raw_data = os.path.join(base_path, "data", "00_raw")

            def collect_data():
                if not os.path.exists(raw_data):
                    os.makedirs(raw_data)
                data = {'mpg': [21, 22, 18], 'wt': [2.5, 2.8, 3.2], 'hp': [110, 105, 120]}
                with open(os.path.join(raw_data, 'mtcars_raw.pkl'), 'wb') as f:
                    pickle.dump(data, f)
                return data

            def main():
                print("Running data_collection...")
                collect_data()

            if __name__ == "__main__":
                main()
        """),
        "s04_preprocessing": dedent("""
            import os, pickle

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            raw_data = os.path.join(base_path, "data", "00_raw")
            interim_data = os.path.join(base_path, "data", "01_interim")

            def preprocess_data(data):
                data['mpg_z'] = [(x - sum(data['mpg'])/len(data['mpg'])) for x in data['mpg']]
                if not os.path.exists(interim_data):
                    os.makedirs(interim_data)
                with open(os.path.join(interim_data, 'mtcars_interim.pkl'), 'wb') as f:
                    pickle.dump(data, f)
                return data

            def main():
                print("Running preprocessing...")
                with open(os.path.join(raw_data, 'mtcars_raw.pkl'), 'rb') as f:
                    data = pickle.load(f)
                preprocess_data(data)

            if __name__ == "__main__":
                main()
        """),
        "s05_modeling": dedent("""
            import os, pickle
            from sklearn.linear_model import LinearRegression
            import numpy as np

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            interim_data = os.path.join(base_path, "data", "01_interim")
            processed_data = os.path.join(base_path, "data", "02_processed")

            def build_model(data):
                model = LinearRegression().fit(np.array(data['wt']).reshape(-1,1), data['mpg'])
                if not os.path.exists(processed_data):
                    os.makedirs(processed_data)
                with open(os.path.join(processed_data, 'model.pkl'), 'wb') as f:
                    pickle.dump(model, f)
                return model

            def main():
                print("Running modeling...")
                with open(os.path.join(interim_data, 'mtcars_interim.pkl'), 'rb') as f:
                    data = pickle.load(f)
                build_model(data)

            if __name__ == "__main__":
                main()
        """),
        "s06_visualization": dedent("""
            import os, pickle
            import matplotlib.pyplot as plt

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            interim_data = os.path.join(base_path, "data", "01_interim")
            processed_data = os.path.join(base_path, "data", "02_processed")
            figures_path = os.path.join(base_path, "results", "figures")

            def visualize(data, model):
                if not os.path.exists(figures_path):
                    os.makedirs(figures_path)
                plt.scatter(data['wt'], data['mpg'])
                plt.plot(data['wt'], model.predict(np.array(data['wt']).reshape(-1,1)), color='red')
                plt.xlabel('Weight')
                plt.ylabel('MPG')
                plt.title('Actual vs Predicted')
                plt.savefig(os.path.join(figures_path, 'actual_vs_predicted.png'))
                plt.close()

            def main():
                print("Running visualization...")
                with open(os.path.join(interim_data, 'mtcars_interim.pkl'), 'rb') as f:
                    data = pickle.load(f)
                with open(os.path.join(processed_data, 'model.pkl'), 'rb') as f:
                    model = pickle.load(f)
                visualize(data, model)

            if __name__ == "__main__":
                main()
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".py", content)

    main_content = dedent("""
        # Main runner

        import s03_data_collection
        import s04_preprocessing
        import s05_modeling
        import s06_visualization

        s03_data_collection.main()
        s04_preprocessing.main()
        s05_modeling.main()
        s06_visualization.main()
    """)
    write_script(folder_path, "s00_main", ".py", main_content)

def create_stata_example(folder_path):
    scripts = {
        "s03_data_collection": dedent("""
            * Data collection code
            global base_path ".."
            global raw_data "$base_path/data/raw"

            program define data_collection_main
                mkdir "$raw_data"
                tempfile temp
                input mpg wt hp
                21 2.5 110
                22 2.8 105
                18 3.2 120
                end
                save "$raw_data/mtcars_raw.dta", replace
                display "Data collection done"
            end
                                      
            data_collection_main
        """),
        "s04_preprocessing": dedent("""
            * Preprocessing code
            global base_path ".."
            global raw_data "$base_path/data/00_raw"
            global interim_data "$base_path/data/01_interim"

            program define preprocessing_main
                mkdir "$interim_data"
                use "$raw_data/mtcars_raw.dta", clear
                gen mpg_z = (mpg - mean(mpg))
                save "$interim_data/mtcars_interim.dta", replace
                display "s04_Preprocessing done"
            end

            preprocessing_main
        """),
        "s05_modeling": dedent("""
            * Modeling code
            global base_path ".."
            global interim_data "$base_path/data/01_interim"
            global processed_data "$base_path/data/02_processed"

            program define modeling_main
                mkdir "$processed_data"
                use "$interim_data/mtcars_interim.dta", clear
                regress mpg wt hp
                estimates save "$processed_data/mtcars_model", replace
                display "Modeling done"
            end

            modeling_main
        """),
        "s06_visualization": dedent("""
            * Visualization code
            global base_path ".."
            global interim_data "$base_path/data/01_interim"
            global processed_data "$base_path/data/02_processed"
            global figures "$base_path/results/figures"

            program define visualization_main
                mkdir "$figures"
                use "$interim_data/mtcars_interim.dta", clear
                scatter mpg wt
                graph export "$figures/actual_vs_predicted.png", replace
                display "Visualization done"
            end

            visualization_main
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".do", content)

    main_content = dedent("""
        * Main runner

        do install_dependencies.do

        do s03_data_collection.do
        do s04_preprocessing.do
        do s05_modeling.do
        do s06_visualization.do

        data_collection_main
        preprocessing_main
        modeling_main
        visualization_main
    """)
    write_script(folder_path, "s00_main", ".do", main_content)

def create_matlab_example(folder_path):
    scripts = {
        "s03_data_collection": dedent("""
            % Data collection code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            raw_data = fullfile(base_path, 'data', '00_raw');

            function s03_data_collection_main()
                if ~exist(raw_data, 'dir')
                    mkdir(raw_data);
                end
                mpg = [21; 22; 18];
                wt = [2.5; 2.8; 3.2];
                hp = [110; 105; 120];
                save(fullfile(raw_data, 'mtcars_raw.mat'), 'mpg', 'wt', 'hp');
                disp('Data collection done');
            end
                                    
            s03_data_collection_main();
                                      
        """),
        "s04_preprocessing": dedent("""
            % Preprocessing code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            raw_data = fullfile(base_path, 'data', '00_raw');
            interim_data = fullfile(base_path, 'data', '01_interim');

            function s04_preprocessing_main()
                if ~exist(interim_data, 'dir')
                    mkdir(interim_data);
                end
                load(fullfile(raw_data, 'mtcars_raw.mat'));
                mpg_z = mpg - mean(mpg);
                save(fullfile(interim_data, 'mtcars_interim.mat'), 'mpg', 'wt', 'hp', 'mpg_z');
                disp('Preprocessing done');
            end

            s04_preprocessing_main();
                                    
        """),
        "s05_modeling": dedent("""
            % Modeling code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            interim_data = fullfile(base_path, 'data', '01_interim');
            processed_data = fullfile(base_path, 'data', '02_processed');

            function s05_modeling_main()
                if ~exist(processed_data, 'dir')
                    mkdir(processed_data);
                end
                load(fullfile(interim_data, 'mtcars_interim.mat'));
                model = fitlm(wt, mpg);
                save(fullfile(processed_data, 'model.mat'), 'model');
                disp('Modeling done');
            end

            s05_modeling_main();
                               
        """),
        "s06_visualization": dedent("""
            % Visualization code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            interim_data = fullfile(base_path, 'data', '01_interim');
            processed_data = fullfile(base_path, 'data', '02_processed');
            figures_path = fullfile(base_path, 'results', 'figures');

            function s06_vvisualization_main()
                if ~exist(figures_path, 'dir')
                    mkdir(figures_path);
                end
                load(fullfile(interim_data, 'mtcars_interim.mat'));
                load(fullfile(processed_data, 'model.mat'));
                scatter(wt, mpg)
                hold on
                plot(wt, predict(model, wt))
                xlabel('Weight')
                ylabel('MPG')
                title('Actual vs Predicted MPG')
                saveas(gcf, fullfile(figures_path, 'actual_vs_predicted.png'))
                hold off
                disp('Visualization done');
            end

            s06_visualization_main();
                                    
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".m", content)

    main_content = dedent("""
        % Main runner

        run('s01_install_dependencies.m')

        s03_vdata_collection_main();
        s04_vpreprocessing_main();
        s05_vmodeling_main();
        s06_vvisualization_main();
    """)
    write_script(folder_path, "s00_main", ".m", main_content)

def create_sas_example(folder_path):
    scripts = {
        "s03_data_collection": dedent("""
            * Data collection code;
            %let base_path = ..;
            %let raw_data = &base_path./data/00_raw;

            %macro data_collection_main();
                libname raw "&raw_data.";
                data raw.mtcars_raw;
                    input mpg wt hp;
                    datalines;
                    21 2.5 110
                    22 2.8 105
                    18 3.2 120
                    ;
                run;
                %put Data collection done;
            %mend;

            %data_collection_main;
        """),
        "s04_preprocessing": dedent("""
            * Preprocessing code;
            %let base_path = ..;
            %let raw_data = &base_path./data/00_raw;
            %let interim_data = &base_path./data/01_interim;

            %macro preprocessing_main();
                libname raw "&raw_data.";
                libname interim "&interim_data.";
                data interim.mtcars_interim;
                    set raw.mtcars_raw;
                    mpg_z = mpg - mean(mpg);
                run;
                %put Preprocessing done;
            %mend;

            %preprocessing_main;
        """),
        "s05_modeling": dedent("""
            * Modeling code;
            %let base_path = ..;
            %let interim_data = &base_path./data/01_interim;
            %let processed_data = &base_path./data/02_processed;

            %macro modeling_main();
                libname interim "&interim_data.";
                libname processed "&processed_data.";
                proc reg data=interim.mtcars_interim outest=processed.model;
                    model mpg = wt hp;
                run;
                %put Modeling done;
            %mend;

            %modeling_main;
        """),
        "s06_visualization": dedent("""
            * Visualization code;
            %let base_path = ..;
            %let interim_data = &base_path./data/01_interim;
            %let figures = &base_path./results/figures;

            %macro visualization_main();
                libname interim "&interim_data.";
                proc sgscatter data=interim.mtcars_interim;
                    plot mpg*wt;
                run;
                /* No direct export to png unless using ODS Graphics */
                %put Visualization done;
            %mend;

            %visualization_main;
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".sas", content)

    main_content = dedent("""
        * Main runner;

        %include "s01_install_dependencies.sas";

        %data_collection_main;
        %preprocessing_main;
        %modeling_main;
        %visualization_main;
    """)
    write_script(folder_path, "s00_main", ".sas", main_content)


@ensure_correct_kernel
def main():

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
  
    # Create scripts and notebook
    print(f"loading {programming_language} code example")
    create_example(programming_language, "./src")
    get_setup_dependencies_main()
    update_readme_main()

    
if __name__ == "__main__":

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()