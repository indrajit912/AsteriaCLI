"""
Setup script for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="asteriacli",
    version="0.1.0",
    author="Indrajit Ghosh",
    author_email="indrajitghosh912@gmail.com",
    description="A unified CLI for managing all AI-related workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indrajit912/AsteriaCLI.git",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
    install_requires=[
        "typer[all]>=0.12.0",
        "rich>=13.7.0",
        "click>=8.1.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.13.0",
        "toml>=0.10.2",
        "tomli-w>=1.0.0",
        "thefuzz>=0.22.1",
        "python-Levenshtein>=0.25.1",
        "google-genai>=2.10.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "asteria=asteria.cli:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
