from setuptools import setup, find_packages

setup(
    name='setup',                # Name of the project
    version='0.1',
    packages=find_packages(),         # This will automatically find your setup package and any sub-packages
    entry_points={
        'console_scripts': [
            'run-backup=setup.run_backup:main',  # The CLI command and entry point
            'set-dataset=setup.set_dataset:main',  # 'set-datasets' is the command to run, points to `main()` in `set_datasets.py`
            'update-requirements=setup.update_requirements:main',
            'get-dependencies=setup.get_dependencies:main',
        ],
    },
)
