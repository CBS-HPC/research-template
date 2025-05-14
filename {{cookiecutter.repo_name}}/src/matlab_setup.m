function matlab_setup()
% setup_matlab_project()
% Initializes a MATLAB project and tracks dependencies for a main file.
%
% - Determines project directory as the parent folder of this script
% - Uses the folder name as the project name
% - Tracks dependencies for main.m inside src/

% --- Determine script and project directory ---
thisScriptPath = mfilename('fullpath');
thisScriptDir  = fileparts(thisScriptPath);
projectDir     = fileparts(thisScriptDir);             % One level up
[~, projectName] = fileparts(projectDir);              % Folder name = project name

% --- Config ---
mainFile    = fullfile(projectDir, "src", "s00_main.m");   % Entry point
depFile     = fullfile(projectDir, "src", "dependencies2.txt");
projectFile = fullfile(projectDir, projectName + ".prj");

% --- Create MATLAB Project if Not Exists ---
if ~isfile(projectFile)
    fprintf("🔧 Creating MATLAB project: %s\n", projectFile);
    proj = matlab.project.createProject(projectDir);
    save(proj, projectFile);
    fprintf("✅ MATLAB project created: %s\n", projectFile);
else
    fprintf("✅ MATLAB project already exists: %s\n", projectFile);
end

% --- Check that main.m exists ---
if ~isfile(mainFile)
    error("❌ Main file not found: %s", mainFile);
end

% --- Track dependencies ---
fprintf("📦 Analyzing dependencies for: %s\n", mainFile);
[files, products] = matlab.codetools.requiredFilesAndProducts(mainFile);

% --- Write file dependencies ---
try
    fid = fopen(depFile, 'w');
    for i = 1:numel(files)
        fprintf(fid, "%s\n", files{i});
    end
    fclose(fid);
    fprintf("📄 Dependencies written to: %s\n", depFile);
catch ME
    warning("⚠️ Failed to write dependency file: %s", ME.message);
end

% --- Display required toolboxes ---
fprintf("\n🔍 Required Toolboxes:\n");
for i = 1:numel(products)
    fprintf(" - %s (v%s)\n", products(i).Name, products(i).Version);
end

end
