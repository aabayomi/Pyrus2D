from setuptools import setup, find_packages

setup(
    name="pyrus-2d-keepaway",
    version="1.0",
    description="Keepaway RL",
    author="Abayomi Adekanmbi",
    author_email="odunayo@email.com",
    packages=find_packages(),
    install_requires=[
        'coloredlogs==15.0.1',
        'humanfriendly==10.0',
        'numpy==1.24.2',
        'pyrusgeom==0.1.2',
        'scipy==1.10.1',
    ],
)

