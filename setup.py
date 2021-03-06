from setuptools import setup, find_packages

version = '0.1'

setup(name='MongoBag',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[],
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='pymongo mongodb mongo colander',
      author='Stefano Fontanelli',
      author_email='s.fontanelli@asidev.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'pymongo',
          'colander >= 0.9.9',
          'mongoq'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      tests_require=[],
      test_suite='tests',
      )
