#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='lex-bot-tester',
      version='0.9.0',
      description='''lex-bot-tester is a library that simplifies
        the creation of AWS Lex Bot tests.
        Using AWS Lex Models Client this utility inspects the properties of
        the available Bots and creates specific Results classes to be used by
        the tests.
        ''',
      license='GPL',
      keywords='amazon aws lex bot tester conversation test automation',
      author='Diego Torres Milano',
      author_email='dtmilano@gmail.com',
      url='https://github.com/dtmilano/lex-bot-tester/',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      package_data={'': ['*.png']},
      include_package_data=True,
      scripts=[],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GPL'],
      install_requires=['setuptools', 'requests'],
      )
