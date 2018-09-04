import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='marple',
    version='0.1dev2',
    packages=setuptools.find_packages(),
    author='Ensoft Ltd',
    author_email='ensoft@ensoft.co.uk',
    description='A Linux profiling multi-tool with visualisation.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='Linux profile profiling perf bcc visualisation',
    package_data={
        '': ['*', '.coveragerc'],
        'marple.collect': ['tools/*/*'],
        'marple.display': ['tools/*/*'],
    },
    url="http://github.com/ensoft/marple/",
    project_urls={
        "Source Code": "http://github.com/ensoft/marple/",
        "Automated testing": "https://travis-ci.org/ensoft/marple/",
        "Code coverage": "https://codecov.io/gh/ensoft/marple/"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Development Status :: 3 - Alpha",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='~=3.6',
    entry_points={
        'console_scripts': [
            'marple=marple.main:main',
            'marple_test=marple.test:main'
        ]
    },
    install_requires=[
        'asynctest>=0.12.2',
        'ipython>=6.5.0',
        'ipython-genutils>=0.2.0',
        'matplotlib>=2.2.2',
        'numpy>=1.13.3',
        'pandas>=0.23.4',
        'pylint>=2.1.1',
        'PyQt5>=5.11.2',
        'PyQt5-sip>=4.19.12',
        'pyqtgraph>=0.10.0',
        'pytest>=3.7.1',
        'pytest-cov>=2.5.1',
        'scipy>=0.19.1',
    ]
)
