# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='nikoniko',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Nikoniko API',
    long_description=readme,
    author='Julio Sangrador-Paton',
    author_email='jsangradorp@gmail.com',
    url='https://github.com/jsangradorp/nikonikoapi',
    license=license,
    install_requires=['bcrypt', 'hug', 'sqlalchemy', 'marshmallow', 'pyjwt', 'psycopg2', 'sqlalchemy_utils'],
    packages=find_packages(exclude=('tests', 'docs'))
)

