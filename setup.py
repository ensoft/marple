# -------------------------------------------------------------
# setup.py - setuptools for packaging MARPLE
# July-Aug 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

import setuptools

with open('docs/README.md', 'r') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    requirements = f.read()
    requirements = requirements.split()


setuptools.setup(
    name='marple',
    version='0.1dev1',
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
    scripts = ['marple/marple_setup'],
    entry_points={
        'console_scripts': [
            'marple=marple.__main__:main',
            'marple_test=marple.test:main'
        ]
    },
    install_requires=requirements
)
