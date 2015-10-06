import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

setup(
    name='score.slang',
    version='0.3.2',
    description='Slang is the markup language of The SCORE Framework',
    long_description=README,
    author='strg.at',
    author_email='score@strg.at',
    url='http://score-framework.org',
    keywords='score framework web slang markup parser',
    packages=['score.slang'],
    install_requires=[
        'ply >= 3.4',
        'lxml',
    ],
)
