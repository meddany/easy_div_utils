from setuptools import setup, find_packages

VERSION = '2.9.3'

# Setting up
setup(
    name="easy_utils_dev",
    version=VERSION,
    packages=find_packages(),
    install_requires=['psutil' , 'ping3'],
    keywords=['python3'],
    classifiers=[
        "Programming Language :: Python :: 3",
    ]
)