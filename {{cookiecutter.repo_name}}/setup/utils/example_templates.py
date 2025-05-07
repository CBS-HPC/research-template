import os
import pathlib
from textwrap import dedent

from .general_tools import *
from .code_templates import write_script
from .readme_templates import main as update_readme_main
from .get_dependencies import main as get_setup_dependencies_main

pip_installer(required_libraries=['rpds-py==0.21.0', 'nbformat'])

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
        "data_collection": dedent("""
            data_collection <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              raw_data <- file.path(base_path, "data", "raw")
              interim_data <- file.path(base_path, "data", "interim")
              processed_data <- file.path(base_path, "data", "processed")
              
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
              
              if (interactive()) { main() }
              
              environment()
            })
        """),
        "preprocessing": dedent("""
            preprocessing <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              raw_data <- file.path(base_path, "data", "raw")
              interim_data <- file.path(base_path, "data", "interim")
              processed_data <- file.path(base_path, "data", "processed")
              
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
              
              if (interactive()) { main() }
              
              environment()
            })
        """),
        "modeling": dedent("""
            modeling <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              interim_data <- file.path(base_path, "data", "interim")
              processed_data <- file.path(base_path, "data", "processed")
              
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
              
              if (interactive()) { main() }
              
              environment()
            })
        """),
        "visualization": dedent("""
            visualization <- local({
              base_path <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
              interim_data <- file.path(base_path, "data", "interim")
              processed_data <- file.path(base_path, "data", "processed")
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
              
              if (interactive()) { main() }
              
              environment()
            })
        """)
    }
    
    for name, content in scripts.items():
        write_script(folder_path, name, ".R", content)
    
    main_content = dedent("""
        # Main runner
        
        #source('install_dependencies.R')
        source('data_collection.R')
        source('preprocessing.R')
        source('modeling.R')
        source('visualization.R')

        data_collection$main()
        preprocessing$main()
        modeling$main()
        visualization$main()
        print("done")
    """)
    write_script(folder_path, "main", ".R", main_content)

def create_python_example(folder_path):
    scripts = {
        "data_collection": dedent("""
            import os, pickle

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            raw_data = os.path.join(base_path, "data", "raw")

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
        "preprocessing": dedent("""
            import os, pickle

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            raw_data = os.path.join(base_path, "data", "raw")
            interim_data = os.path.join(base_path, "data", "interim")

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
        "modeling": dedent("""
            import os, pickle
            from sklearn.linear_model import LinearRegression
            import numpy as np

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            interim_data = os.path.join(base_path, "data", "interim")
            processed_data = os.path.join(base_path, "data", "processed")

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
        "visualization": dedent("""
            import os, pickle
            import matplotlib.pyplot as plt

            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            interim_data = os.path.join(base_path, "data", "interim")
            processed_data = os.path.join(base_path, "data", "processed")
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

        import data_collection
        import preprocessing
        import modeling
        import visualization

        data_collection.main()
        preprocessing.main()
        modeling.main()
        visualization.main()
    """)
    write_script(folder_path, "main", ".py", main_content)

def create_stata_example(folder_path):
    scripts = {
        "data_collection": dedent("""
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

            if ("${interactive}" != "") {
                data_collection_main
            }
        """),
        "preprocessing": dedent("""
            * Preprocessing code
            global base_path ".."
            global raw_data "$base_path/data/raw"
            global interim_data "$base_path/data/interim"

            program define preprocessing_main
                mkdir "$interim_data"
                use "$raw_data/mtcars_raw.dta", clear
                gen mpg_z = (mpg - mean(mpg))
                save "$interim_data/mtcars_interim.dta", replace
                display "Preprocessing done"
            end

            if ("${interactive}" != "") {
                preprocessing_main
            }
        """),
        "modeling": dedent("""
            * Modeling code
            global base_path ".."
            global interim_data "$base_path/data/interim"
            global processed_data "$base_path/data/processed"

            program define modeling_main
                mkdir "$processed_data"
                use "$interim_data/mtcars_interim.dta", clear
                regress mpg wt hp
                estimates save "$processed_data/mtcars_model", replace
                display "Modeling done"
            end

            if ("${interactive}" != "") {
                modeling_main
            }
        """),
        "visualization": dedent("""
            * Visualization code
            global base_path ".."
            global interim_data "$base_path/data/interim"
            global processed_data "$base_path/data/processed"
            global figures "$base_path/results/figures"

            program define visualization_main
                mkdir "$figures"
                use "$interim_data/mtcars_interim.dta", clear
                scatter mpg wt
                graph export "$figures/actual_vs_predicted.png", replace
                display "Visualization done"
            end

            if ("${interactive}" != "") {
                visualization_main
            }
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".do", content)

    main_content = dedent("""
        * Main runner

        do install_dependencies.do

        do data_collection.do
        do preprocessing.do
        do modeling.do
        do visualization.do

        data_collection_main
        preprocessing_main
        modeling_main
        visualization_main
    """)
    write_script(folder_path, "main", ".do", main_content)

def create_matlab_example(folder_path):
    scripts = {
        "data_collection": dedent("""
            % Data collection code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            raw_data = fullfile(base_path, 'data', 'raw');

            function data_collection_main()
                if ~exist(raw_data, 'dir')
                    mkdir(raw_data);
                end
                mpg = [21; 22; 18];
                wt = [2.5; 2.8; 3.2];
                hp = [110; 105; 120];
                save(fullfile(raw_data, 'mtcars_raw.mat'), 'mpg', 'wt', 'hp');
                disp('Data collection done');
            end

            if ~isdeployed
                data_collection_main();
            end
        """),
        "preprocessing": dedent("""
            % Preprocessing code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            raw_data = fullfile(base_path, 'data', 'raw');
            interim_data = fullfile(base_path, 'data', 'interim');

            function preprocessing_main()
                if ~exist(interim_data, 'dir')
                    mkdir(interim_data);
                end
                load(fullfile(raw_data, 'mtcars_raw.mat'));
                mpg_z = mpg - mean(mpg);
                save(fullfile(interim_data, 'mtcars_interim.mat'), 'mpg', 'wt', 'hp', 'mpg_z');
                disp('Preprocessing done');
            end

            if ~isdeployed
                preprocessing_main();
            end
        """),
        "modeling": dedent("""
            % Modeling code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            interim_data = fullfile(base_path, 'data', 'interim');
            processed_data = fullfile(base_path, 'data', 'processed');

            function modeling_main()
                if ~exist(processed_data, 'dir')
                    mkdir(processed_data);
                end
                load(fullfile(interim_data, 'mtcars_interim.mat'));
                model = fitlm(wt, mpg);
                save(fullfile(processed_data, 'model.mat'), 'model');
                disp('Modeling done');
            end

            if ~isdeployed
                modeling_main();
            end
        """),
        "visualization": dedent("""
            % Visualization code
            base_path = fullfile(fileparts(mfilename('fullpath')), '..');
            interim_data = fullfile(base_path, 'data', 'interim');
            processed_data = fullfile(base_path, 'data', 'processed');
            figures_path = fullfile(base_path, 'results', 'figures');

            function visualization_main()
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

            if ~isdeployed
                visualization_main();
            end
        """)
    }

    for name, content in scripts.items():
        write_script(folder_path, name, ".m", content)

    main_content = dedent("""
        % Main runner

        run('install_dependencies.m')

        data_collection_main();
        preprocessing_main();
        modeling_main();
        visualization_main();
    """)
    write_script(folder_path, "main", ".m", main_content)

def create_sas_example(folder_path):
    scripts = {
        "data_collection": dedent("""
            * Data collection code;
            %let base_path = ..;
            %let raw_data = &base_path./data/raw;

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
        "preprocessing": dedent("""
            * Preprocessing code;
            %let base_path = ..;
            %let raw_data = &base_path./data/raw;
            %let interim_data = &base_path./data/interim;

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
        "modeling": dedent("""
            * Modeling code;
            %let base_path = ..;
            %let interim_data = &base_path./data/interim;
            %let processed_data = &base_path./data/processed;

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
        "visualization": dedent("""
            * Visualization code;
            %let base_path = ..;
            %let interim_data = &base_path./data/interim;
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

        %include "install_dependencies.sas";

        %data_collection_main;
        %preprocessing_main;
        %modeling_main;
        %visualization_main;
    """)
    write_script(folder_path, "main", ".sas", main_content)


#@ensure_correct_kernel
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