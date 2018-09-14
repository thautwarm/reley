from setuptools import setup
from Redy.Tools.Version import Version
from Redy.Tools.PathLib import Path

with open('./README.md', encoding='utf-8') as f:
    readme = f.read()

version_filename = 'next_version'
with open(version_filename) as f:
    version = Version(f.read().strip())

with Path("./reley/__release_info__.py").open('w') as f:
    f.write('__VERSION__ = {}\n__AUTHOR__ = "thautwarm"'.format(
        repr(str(version))))

setup(
    name='reley',
    version=str(version),
    keywords='haskell, language, static typed, compiled',
    description=
    'A static compiled language on Python with type safety, efficiency and syntax sugars.',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/thautwarm/reley',
    author='thautwarm',
    author_email='twshere@outlook.com',
    packages=['reley'],
    entry_points={'console_scripts': ['reley=reley.cli:main']},
    package_data={'reley': ['grammar.rbnf']},
    install_requires=['Redy', 'rbnf>=0.3.21', 'wisepy'],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)

version.increment(version_number_idx=2, increment=1)
if version[2] is 42:
    version.increment(version_number_idx=1, increment=1)
if version[1] is 42:
    version.increment(version_number_idx=0, increment=1)

with open(version_filename, 'w') as f:
    f.write(str(version))
