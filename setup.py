#!/usr/bin/env python3
import os
import sys
from setuptools import setup

if sys.argv[-1] == 'publish':
    if os.system("pip3 freeze | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    os.system("python3 setup.py sdist upload")
    os.system("python3 setup.py bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a {0} -m 'version {0}'".format(__version__))
    print("  git push --tags")
    sys.exit()

setup(
    name="lepton-vm",
    version="0.1.0",
    author="Ale",
    author_email="hi@ale.rocks",
    description="A universal runtime version manager",
    url="https://github.com/iamale/lepton",
    packages=["lepton_vm"],
    install_requires=[
        "Click==6.4",
        "requests==2.10.0",
    ],
    entry_points="""
        [console_scripts]
        lepton=lepton_vm:cli
    """,
)
