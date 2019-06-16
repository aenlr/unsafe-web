from setuptools import setup, find_packages

requires = [
    'bcrypt',
    'passlib',
    'paste',
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'python-dateutil',
    'waitress',
]

testing_extras = [
    'beautifulsoup4',
    'pytest',
    'pytest-cov',
    'pytest-runner',
    'webtest >= 1.3.1',
]

docs_extras = [
    'Sphinx >= 1.8.1',
    'docutils'
]

dev_extras = testing_extras  # + docs_extras

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
      url='https://github.com/anob3it/unsafe-web',
      keywords='web pyramid xss csrf security',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      extras_require={'dev': dev_extras, 'testing': testing_extras, 'docs': docs_extras},
      entry_points={
          'console_scripts': [
              'unsafe-initdb = unsafe.scripts.initdb:main',
              'unsafe-purge-sessions = unsafe.scripts.purge_sessions:main',
              'unsafe = unsafe.scripts.runner:main'
          ],
          'paste.app_factory': [
              'main = unsafe:main',
          ],
      }
)
