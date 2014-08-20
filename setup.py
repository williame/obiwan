import os
from setuptools import setup

setup(name="obiwan",
    version="1.0.6",
    description="A runtime type checker (contract system) and JSON validator",
    author="William Edwards",
    author_email="willvarfar@gmail.com",
    url="https://github.com/williame/obiwan",
    long_description=os.popen("pandoc -t rst README.md").read(),
    packages=["obiwan"])

