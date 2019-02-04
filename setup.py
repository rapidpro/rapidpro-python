from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst', 'md')
except ImportError:
    print("Warning: pypandoc module not found, could not convert Markdown to RST")
    long_description = open('README.md', 'r').read()


def _is_requirement(line):
    """Returns whether the line is a valid package requirement."""
    line = line.strip()
    return line and not (line.startswith("-r") or line.startswith("#"))


def _read_requirements(filename):
    """Returns a list of package requirements read from the file."""
    requirements_file = open(filename).read()
    return [line.strip() for line in requirements_file.splitlines()
            if _is_requirement(line)]


required_packages = _read_requirements("requirements/base.txt")
test_packages = _read_requirements("requirements/tests.txt")

setup(
    name='rapidpro-python',
    version=__import__('temba_client').__version__,
    description='Python client library for the RapidPro',
    long_description=long_description,

    keywords='rapidpro client',
    url='https://github.com/rapidpro',
    license='BSD',

    author='Nyaruka',
    author_email='code@nyaruka.com',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],

    packages=find_packages(),
    install_requires=required_packages,

    test_suite='nose.collector',
    tests_require=required_packages + test_packages,
)
