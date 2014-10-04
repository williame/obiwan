import os
from setuptools import setup

setup(name="obiwan",
    version="1.0.8",
    description="A runtime type checker (contract system) and JSON validator",
    author="William Edwards",
    author_email="willvarfar@gmail.com",
    url="https://github.com/williame/obiwan",
    long_description=os.popen("pandoc -t rst README.md").read(),
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3.4",
    ),
    packages=["obiwan"])

