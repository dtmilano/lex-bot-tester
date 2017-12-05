#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='lex-bot-tester',
      version='0.9.2',
      description='''lex-bot-tester is a library that simplifies the creation of AWS Lex Bot tests.''',
      long_description='''Using AWS Lex Models Client this utility inspects the properties of
        the available Bots and creates specific Results classes to be used by the tests.
        ''',
      license='GPL-3.0',
      keywords='amazon aws lex bot tester conversation test automation',
      author='Diego Torres Milano',
      author_email='dtmilano@gmail.com',
      url='https://github.com/dtmilano/lex-bot-tester/',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      # package_data={'': ['*.png']},
      # include_package_data=True,
      # scripts=[],
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
