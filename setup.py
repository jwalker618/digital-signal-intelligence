"""
Digital Signal Intelligence - Insurance Pricing Platform
Setup configuration for package installation

Note: Primary configuration is in pyproject.toml. This file provides
backwards compatibility for editable installs (pip install -e .).
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="digital-signal-intelligence",
    version="0.2.0",
    author="John Walker",
    author_email="johnea.walker@outlook.com",
    description="Insurance technical pricing using digital signal analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jwalker618/digital-signal-intelligence",
    packages=find_packages(include=[
        "signals", "signals.*",
        "layers", "layers.*",
        "coverages", "coverages.*",
        "api", "api.*",
        "analytics", "analytics.*",
        "orchestration", "orchestration.*",
        "discovery", "discovery.*",
        "integrations", "integrations.*",
        "builder", "builder.*",
        "db", "db.*",
    ]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "isort>=5.12.0",
        ],
        "scraping": [
            "beautifulsoup4>=4.12.0",
            "selenium>=4.10.0",
            "requests>=2.31.0",
        ],
        "api": [
            "flask>=3.0.0",
            "flask-restx>=1.3.0",
            "flask-cors>=4.0.0",
            "gunicorn>=21.2.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "redis>=5.0.0",
        ],
        "cloud": [
            "boto3>=1.28.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
