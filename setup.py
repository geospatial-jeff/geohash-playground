from setuptools import setup, find_packages


setup(
    name='geohash-query-benchmark',
    author='Jeff Albrecht',
    author_email='jeffalbrecht9@gmail.com',
    version=0.1,
    url='https://github.com/geospatial-jeff/geohash-playground',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['benchmark=geohash_utils.benchmark.benchmark_runner:cli']
    }
)