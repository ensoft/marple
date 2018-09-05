import setuptools

setuptools.setup(
    name='marple.core',
    version='0.1dev3',
    packages=['marple.common'],
    author='Ensoft Ltd',
    author_email='ensoft@ensoft.co.uk',
    description='',
    package_data={
        'marple': [
            '.coveragerc',
            'config.txt',
            'main.py',
            'marple_setup',
            'pylintrc.txt',
            'marple_test.py',
            '*'
        ],
        '': ['*']
    },
    url="http://github.com/ensoft/marple/",
    python_requires='~=3.6',
    scripts=['marple/marple_setup'],
    entry_points={
        'console_scripts': [
            'marple=marple.common.main:main',
            'marple_test=marple.common.marple_test:main'
        ]
    },
    install_requires=[
        'asynctest>=0.12.2',
        'pylint>=2.1.1',
        'pytest>=3.7.1',
        'pytest-cov>=2.5.1',
    ]
)
