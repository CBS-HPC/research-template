from setuptools import setup, find_packages

setup(
    name='setup',                # Name of the project
    version='1.0',
    py_modules=['run_backup', 'set_dataset', 'update_requirements','get_dependencies','install_dependencies','deic_storage_download','run_setup'],  # Directly specify the modules
    #packages=find_packages(),         # This will automatically find your setup package and any sub-packages
    entry_points={
        'console_scripts': [
            'run-backup=run_backup:main',  # The CLI command and entry point
            'set-dataset=set_dataset:main',  # 'set-datasets' is the command to run, points to `main()` in `set_datasets.py`
            'update-requirements=update_requirements:main',
            'get-dependencies=get_dependencies:main',
            'install-dependencies=install_dependencies:main',
            'deic-storage-download=deic_storage_download:main',
            'run-setup=run_setup:main',
        ],
    },
    install_requires=[
        'python-dotenv',
        'pyyaml',
        'requests',
        'rpds-py==0.21.0',
        'nbformat',
        'beautifulsoup4',
    ],
)
