function matlab_setup()
    % setup_matlab_project()
    % Initializes a MATLAB project and tracks dependencies for all .m files in the src/ folder.
    %
    % - Determines project directory as the parent folder of this script
    % - Uses the folder name as the project name
    % - Tracks dependencies for all .m files in src/

    % --- Determine script and project directory ---
    thisScriptPath = mfilename('fullpath');
    thisScriptDir  = fileparts(thisScriptPath);
    projectDir     = fileparts(thisScriptDir);             % One level up
    [~, projectName] = fileparts(projectDir);              % Folder name = project name
    
    % --- Print Project Name ---
    fprintf("🔧 Setting up MATLAB project: %s\n", projectName);

    % --- Config ---
    depFile     = fullfile(projectDir, "src", "dependencies2.txt");
    projectFile = fullfile(projectDir, projectName + ".prj");
    
    % --- Create MATLAB Project if Not Exists ---
    if ~isfile(projectFile)
        fprintf("🔧 Creating MATLAB project: %s\n", projectFile);
        try
            proj = matlab.project.createProject("Name",projectName,"Folder",projectDir);
            save(proj);
            disp('Project saved successfully!');
        catch ME
            disp(['Error saving project: ', ME.message]);
        end
        fprintf("✅ MATLAB project created: %s\n", projectFile);
    else
        fprintf("✅ MATLAB project already exists: %s\n", projectFile);
    end

    % --- Track dependencies for all .m files in src ---
    mFiles = dir(fullfile(projectDir, 'src', '*.m'));
    allFiles = {};
    allProducts = [];
    
    for i = 1:length(mFiles)
        mFilePath = fullfile(mFiles(i).folder, mFiles(i).name);
        
        try
            fprintf("📦 Analyzing dependencies for: %s\n", mFilePath);
            [files, products] = matlab.codetools.requiredFilesAndProducts(mFilePath);
            
            % Append files and products
            allFiles = [allFiles, files];
            allProducts = [allProducts, products];
        catch ME
            % Skip files with syntax errors and continue
            fprintf("⚠️ Skipping file due to error: %s\n", mFilePath);
            fprintf("Error message: %s\n", ME.message);
        end
    end

    % --- Write file dependencies and products ---
    fid = fopen(depFile, 'w');

    try
        % Write file dependencies
        fprintf(fid, "📂 File Dependencies:\n");
        for i = 1:numel(allFiles)
            fprintf(fid, "%s\n", allFiles{i});
        end
        
        % Write products (toolboxes)
        fprintf(fid, "\n🔧 Required Toolboxes:\n");
        for i = 1:numel(allProducts)
            fprintf(fid, "%s (v%s)\n", allProducts(i).Name, allProducts(i).Version);
        end
        
        fprintf("📄 Dependencies and products written to: %s\n", depFile);
    catch ME
        warning("⚠️ Failed to write dependency file: %s", ME.message);
    end
    fclose(fid);
end
