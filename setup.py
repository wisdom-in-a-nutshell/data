from setuptools import setup, find_packages

setup(
    name="ai-data-processor",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "nltk==3.6.5",
        "python-slugify==5.0.2",
        "pyyaml==5.4.1",
        "pytest==7.3.1",  # Added pytest for testing
    ],
    entry_points={
        "console_scripts": [
            "process-data=main:main",
        ],
    },
)