from setuptools import setup, find_packages

# Install and runtime requirements
install_requires = [
    'bcrypt',
    'passlib',
    'paste',
    'pyramid',
    'pyramid_jinja2',
    'python-dateutil',
    'waitress',
]

# Unit test dependencies
tests_require = [
    'beautifulsoup4',
    'pytest >= 4.6.3',
    'webtest >= 2.0.33',
]

# Extras for unit tests
testing_extras = tests_require + [
    'pytest-cov >= 2.7.1'
]

# Extras for development (unit testing, debugging aids)
dev_extras = testing_extras + ['pyramid_debugtoolbar']

# Extras for quality assurance
qa_extras = testing_extras + [
    'flake8',
    'mypy',
]

# Extras for generating documentation
docs_extras = [
    'Sphinx >= 1.8.1',
    'docutils'
]

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
      author_email='anob3it@users.noreply.github.com',
      url='https://github.com/anob3it/unsafe-web',
      keywords=['web', 'pyramid', 'xss', 'csrf', 'security'],
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
          'dev': dev_extras,
          'docs': docs_extras,
          'qa': qa_extras,
          'testing': testing_extras,
      },
      #setup_requires=['pytest-runner'],
      tests_require=tests_require,
      entry_points={
          'console_scripts': [
              'unsafe-initdb = unsafe.scripts.initdb:main',
              'unsafe-sessions = unsafe.scripts.sessions:main',
              'unsafe = unsafe.scripts.runner:main'
          ],
          'paste.app_factory': [
              'main = unsafe:main',
          ],
      }
)
