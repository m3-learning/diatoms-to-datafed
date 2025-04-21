"""
    Setup file for diatoms-to-datafed.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 4.6.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""

from setuptools import setup, find_packages

setup(
    name="diatoms-to-datafed",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "datafed>=1.0.0",
        "schedule>=1.1.0",
        "pyyaml>=6.0",
        "pathlib>=1.0.1",
        "typing-extensions>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "diatoms-to-datafed=diatoms_to_datafed.__main__:main",
        ],
    },
    python_requires=">=3.9",
)
