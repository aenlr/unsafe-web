from setuptools import setup, find_packages

requires = [
    'passlib',
    'paste',
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'waitress',
]

testing_extras = [
    'webtest >= 1.3.1'
    'pytest',
    'pytest-cov',
    'pytest-runner'
]

docs_extras = [
    'Sphinx >= 1.8.1',
    'docutils'
]

dev_extras = testing_extras + docs_extras

setup(name='unsafe',
      version='0.1',
      description='Demonstrate unsafe web practices',
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Anders Norlander',
      url='',
      keywords='web pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      setup_requires=['pytest-runner'],
      extras_require={'dev': dev_extras, 'testing': testing_extras, 'docs': docs_extras},
      entry_points="""\
      [paste.app_factory]
      main = unsafe:main
      """,
      )
