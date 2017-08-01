from setuptools import setup, find_packages


install_requires = [
    'SQLAlchemy',
    'SQLAlchemy-Utils',
    'psycopg2',
]
tests_require = []
lint_requires = [
    'pep8',
    'pyflakes',
]
dependency_links = []
setup_requires = []
extras_require = {
    'test': tests_require,
    'all': install_requires + tests_require,
    'lint': lint_requires,
}
classifiers = [
    'Programming Language :: Python :: 3',
]


setup(
    name='jcssutils',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require=extras_require,
    dependency_links=dependency_links,
    classifiers=classifiers,
)
