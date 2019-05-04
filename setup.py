from setuptools import setup, find_packages

setup(
    name='zfs',
    version='0.1',
    license='2-clause BSD',
    author='Colin Valliant',
    author_email='alcarithemad@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        zexplore=explore:cli
    ''',
)
