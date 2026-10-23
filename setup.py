#!/usr/bin/env python3
"""
Setup script for Brazilian Boleto Number Extractor
"""

import re
from setuptools import setup, find_packages

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Single source for the version: the package itself. Parsed rather than imported,
# since the dependencies may not be installed yet.
def read_version():
    with open("boleto_extractor/__init__.py", "r", encoding="utf-8") as fh:
        return re.search(r'^__version__ = "([^"]+)"', fh.read(), re.M).group(1)

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="boleto-extractor",
    version=read_version(),
    author="Pedro",
    author_email="",
    description="A Python library to extract boleto numbers from Brazilian boleto PDF files",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/pedrinho/boleto_extractor",
    # AGPL because PyMuPDF, a required dependency, is.
    license="AGPL-3.0-or-later",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
    ],
    python_requires=">=3.12",
    install_requires=read_requirements(),
    extras_require={
        # Kept in sync with requirements-dev.txt.
        "dev": [
            "pytest==9.1.1",
            "pytest-cov==7.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "boleto-extractor=boleto_extractor.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 