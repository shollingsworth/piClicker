#!/usr/bin/env python
# -*- coding: utf-8 -*-
# using helpful guide at: http://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/quickstart.html
import sys
from glob import glob
from os.path import splitext, basename
try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import find_packages, setup
version = open('VERSION', 'r').read().strip()

author = 'Steven Hollingsworth'
author_email = 'hollingsworth.stevend@gmail.com'

if "{}{}".format(sys.version_info.major, sys.version_info.minor) != '27':
    raise Exception("Error we need to run on python version 2.7 Running on: {}".format(sys.version))

setup(
    name='piClicker',
    version=version,
    url='https://github.com/shollingsworth/piClicker',
    author=author,
    author_email=author_email,
    maintainer=author,
    maintainer_email=author_email,
    description='Emit sounds to find foxes (and break into them in legal test environments)',
    scripts=glob('bin/*.py') + glob('bin/*.sh'),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    install_requires=[
        'pyalsaaudio',
        'psutil',
        'wifi',
        'PyRIC',
        'flask',
        'netifaces',
        'transitions',
        'requests',
    ],
)
