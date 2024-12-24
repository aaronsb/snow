from setuptools import setup, find_packages
from pathlib import Path

# Read README.md for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="snow_sim",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "blessed",
        "numpy",
        "PyYAML",
    ],
    entry_points={
        'console_scripts': [
            'snow-sim=snow_sim.main:main',
        ],
    },
    author="Aaron Bockelie",
    author_email="aaronsb@gmail.com",  # Optional: Add your email if you want
    description="A terminal-based snow particle simulation with realistic physics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="simulation, particles, terminal, snow, physics",
    url="https://github.com/yourusername/snow-sim",  # Replace with actual repo URL
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Games/Entertainment :: Simulation",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "snow_sim": ["config.yaml", "docs/*.md"],
    },
)
