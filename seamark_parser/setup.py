from setuptools import setup, find_packages

setup(
    name="seamark-ecom-parser",
    version="0.1.0",
    description="A simple tool to clean up messy data for SQL databases.",
    author="Seamark Global Innovations",
    packages=find_packages(),
    install_requires=[], # no extra dependencies needed, using standard built-ins
)