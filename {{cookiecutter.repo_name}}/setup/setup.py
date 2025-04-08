from setuptools import setup, find_packages

setup(
    name='setup',                # Name of the project
    version='1.0',
    packages=find_packages(),         # This will automatically find your setup package and any sub-packages
    entry_points={
        'console_scripts': [
            'run-backup=run_backup:main',  # The CLI command and entry point
            'set-dataset=set_dataset:main',  # 'set-datasets' is the command to run, points to `main()` in `set_datasets.py`
            'update-requirements=update_requirements:main',
            'get-dependencies=get_dependencies:main',
            'install-dependencies=install_dependencies:main',
            'deic-download=your_package.deic_storage:main',
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
