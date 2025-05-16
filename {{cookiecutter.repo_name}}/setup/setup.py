from setuptools import setup, find_packages

setup(
    name='setup',
    version='1.0',
    packages=find_packages(where="."),
    package_dir={'': '.'},
    entry_points={
        'console_scripts': [
            'push-backup=utils.backup_tools:main',
            'set-dataset=utils.set_dataset:main',
            'update-dependencies=utils.get_dependencies:main',
            'install-dependencies=utils.install_dependencies:main',
            'deic-storage-download=utils.deic_storage_download:main',
            'run-setup=utils.run_setup:main',
            'update-readme=utils.readme_templates:main',
            'reset-templates=utils.code_templates:main',
            'code-examples=utils.example_templates:main'
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