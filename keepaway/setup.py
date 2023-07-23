import os
from setuptools import setup, find_packages

from pathlib import Path

os.chdir(Path(__file__).parent.absolute())

setup(
    name="keepaway",
    version="1.0",
    description="Keepaway RL",
    author="Abayomi Adekanmbi",
    author_email="odunayo@email.com",
    packages=find_packages(include=["base", "lib.*"]),
    # package_dir={"keepaway_rl": "keepaway/"},
    install_requires=[
        # Add your required dependencies here
        "coloredlogs==15.0.1",
        "humanfriendly==10.0",
        "numpy==1.24.2",
        "pyrusgeom==0.1.2",
        "scipy==1.10.1",
    ],
)
