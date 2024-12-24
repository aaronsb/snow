from setuptools import setup, find_packages

setup(
    name="snow_sim",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "blessed",
        "numpy",
        "PyYAML",  # Added for configuration file support
    ],
    entry_points={
        'console_scripts': [
            'snow-sim=snow_sim.main:main',
        ],
    },
    author="Aaron",
    description="A terminal-based snow simulation",
    python_requires=">=3.6",
)
