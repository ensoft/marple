import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='marple',
    version='0.1dev3',
    packages=['marple'],
    author='Ensoft Ltd',
    author_email='ensoft@ensoft.co.uk',
    description='A Linux profiling multi-tool with visualisation.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='Linux profile profiling perf bcc visualisation',
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
    install_requires=[
        'marple_core',
        'marple_collect',
        'marple_display'
    ]
)
