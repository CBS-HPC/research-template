from setuptools import setup, find_packages

setup(
    name='setup',
    version='1.0',
    packages=find_packages(where="."),
    package_dir={'': '.'},
    entry_points={
        'console_scripts': [
            'run-backup=commands.run_backup:main',
            'set-dataset=commands.set_dataset:main',
            'update-requirements=commands.update_requirements:main',
            'get-dependencies=commands.get_dependencies:main',
            'install-dependencies=commands.install_dependencies:main',
            'deic-storage-download=commands.deic_storage_download:main',
            'run-setup=commands.run_setup:main',
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