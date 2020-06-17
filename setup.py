from setuptools import setup
import re

requirements = []
#with open('requirements.txt') as f:
#  requirements = f.read().splitlines()

# PYK has no requirements!

version = ''
with open('pyk/__init__.py') as f:
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

readme = ''
with open('README.md') as f:
    readme = f.read()

setup(name='pyk',
      author='IAmTomahawkx',
      author_email="iamtomahawkx@gmail.com",
      url='https://github.com/IAmTomahawkx/pyk',
      project_urls={
#        "Documentation": "",
        "Issue tracker": "https://github.com/IAmTomahawkx/pyk/issues",
      },
      version=version,
      packages=['pyk'],
      license='MIT',
      description='a simple, easy to understand language with easy integration capabilities.',
      long_description=readme,
      long_description_content_type="text/markdown",
      include_package_data=True,
      install_requires=requirements,
      python_requires='>=3.5.3',
      classifiers=[
        'Development Status :: Unstable',
        'License :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
      ]
)