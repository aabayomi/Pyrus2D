
import setuptools
from setuptools import find_namespace_packages , find_packages


setuptools.setup(
    name="keepaway",
    version="0.1.0",
    description=('A package for Robocup2D Keepaway - RL environment keepaway.based on '
                 'open-source game Pyrus 2D Soccer Simulator.'),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Abayomi Adekanmbi",
    author_email="odunayo@email.com",
    url='https://github.com/aabayomi/keepaway',
    packages=find_packages(),
    package_dir={'keepaway': 'keepaway/'},
    install_requires=[
        'coloredlogs==15.0.1',
        'humanfriendly==10.0',
        'numpy==1.24.2',
        'pyrusgeom==0.1.2',
        'scipy==1.10.1',
    ],
    package_data={"": ["keepaway/config/server-config.yml"]},
    include_package_data=True,
)
