import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

setup(
    name='score.slang',
    version='0.3.6',
    description='Slang is the markup language of The SCORE Framework',
    long_description=README,
    author='strg.at',
    author_email='score@strg.at',
    url='http://score-framework.org',
    keywords='score framework web slang markup parser',
    packages=['score', 'score.slang'],
    namespace_packages=['score'],
    zip_safe=False,
    license='LGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General '
            'Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=[
        'ply >= 3.4',
        'lxml',
    ],
)
