import os
import os.path

from setuptools import setup, find_packages


root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')


setup(
    name='humanmark',
    packages=find_packages(),
    version='0.4.1',
    description='Human-friendly markdown.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='http://github.com/TkTech/humanmark',
    keywords=['markdown'],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-watch',
            'pytest-cov'
        ],
        'cli': [
            'click'
        ],
        'release': [
            'sphinx',
            'sphinx-click',
            'furo',
            'twine',
            'ghp-import',
            'bump2version'
        ]
    },
    install_requires=[
        'markdown-it-py'
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'humanmark=humanmark.cli:cli'
        ],
        'humanmark.renderers': (
            'markdown = humanmark.render.markdown:MarkdownRenderer\n'
            'json = humanmark.render.json:JSONRenderer\n'
            'txt = humanmark.render.txt:TXTRenderer'
        ),
        'humanmark.backends': (
            'markdown_it = humanmark.backends.markdown_it:MarkdownItBackend'
        )
    }
)
