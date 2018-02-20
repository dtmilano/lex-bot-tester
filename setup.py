#!/usr/bin/env python

import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

README_PATH = os.path.join(HERE, 'README.rst')
try:
    with open(README_PATH) as fd:
        README = fd.read()
except IOError:
    README = ''

setup(name='lex-bot-tester',
      version='1.0.2',
      description='''lex-bot-tester is a library that simplifies the creation of Amazon Alexa Skills and AWS Lex Bot tests.''',
      long_description=README,
      license='GPL-3.0',
      keywords='amazon aws lex bot tester conversation test automation',
      author='Diego Torres Milano',
      author_email='dtmilano@gmail.com',
      url='https://github.com/dtmilano/lex-bot-tester/',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      # package_data={'': ['*.png']},
      # include_package_data=True,
      scripts=['tools/urutu'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   # Indicate who your project is intended for
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Build Tools',
                   # License
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   # Specify the Python versions you support here. In particular, ensure
                   # that you indicate whether you support Python 2, Python 3 or both.
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   ],
      install_requires=['setuptools', 'requests', 'six', 'boto3'],
      )
