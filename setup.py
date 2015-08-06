try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
requirements = open('requirements.txt').read().splitlines()
test_requirements = requirements + ['flake8']

setup(name='qsub_pywrap',
      version='0.0.1',
      description='Execute python functions as qsub jobs.',
      long_description=readme + '\n\n' + history,
      author='Jelle Aalbers',
      author_email='j.aalbers@uva.nl',
      url='https://github.com/jelleaalbers/qsub_pywrap',
      license='MIT',
      py_modules=['qsub_pywrap'],
      install_requires=requirements,
      keywords='qsub,PBS,TORQUE',
      #test_suite='tests',
      #tests_require=test_requirements,
      classifiers=['Intended Audience :: Developers',
                   'Development Status :: 3 - Alpha',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3'],
      zip_safe=False)
