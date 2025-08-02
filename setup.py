#!/usr/bin/env python3
"""
Setup script for Mining Intelligence System
"""

from setuptools import setup, find_packages
import pathlib

# Read the contents of README file
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

# Read requirements
def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

requirements = read_requirements('requirements.txt')
dev_requirements = read_requirements('requirements-dev.txt')

setup(
    name="mining-intelligence-system",
    version="1.0.0",
    author="Mining Intelligence Team",
    author_email="mining-intel@example.com",
    description="Comprehensive mining industry intelligence and data collection system",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/mining-intelligence-system",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/mining-intelligence-system/issues",
        "Documentation": "https://github.com/your-username/mining-intelligence-system/wiki",
        "Source Code": "https://github.com/your-username/mining-intelligence-system",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    keywords="mining, finance, data-collection, web-scraping, business-intelligence, tsx, tsxv",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "testing": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mining-intel=src.core.complete_mining_intelligence_system:main",
            "mining-report=src.reports.daily_tsx_mining_report:main",
            "mining-scraper=src.scrapers.enhanced_mining_scraper:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
)