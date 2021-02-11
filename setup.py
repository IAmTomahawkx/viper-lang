from setuptools import setup
import re
import os

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    requirements = f.readlines()

with open('viper/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

with open('README.rst') as f:
    readme = f.read()

setup(name='viper-lang',
      author='IAmTomahawkx',
      author_email="iamtomahawkx@gmail.com",
      url='https://github.com/IAmTomahawkx/viper-lang',
      project_urls={
#        "Documentation": "",
        "Issue tracker": "https://github.com/IAmTomahawkx/viper-lang/issues",
      },
      version=version,
      packages=['viper', 'viper.exts', 'viper.lib'],
      license='MIT',
      description='a simple, easy to understand language with easy integration capabilities.',
      long_description=readme,
      include_package_data=True,
      install_requires=requirements,
      python_requires='>=3.6.0',
      classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)