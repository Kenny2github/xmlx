from setuptools import setup, find_packages

with open('README.rst', 'r') as f:
    ldesc = f.read()

setup(
    name='xmlx',
    version='0.0.1',
    description='A simple and compact XML parser.',
    long_description=ldesc,
    url='https://github.com/Kenny2github/xmlx',
    author='Ken Hilton',
    author_email='kenny2minecraft@gmail.com',
    license='GNU GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Software Development :: Compilers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='xml dict parser',
    py_modules=['xmlx']
)
