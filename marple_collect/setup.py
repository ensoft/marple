import setuptools

setuptools.setup(
    name='marple.collect',
    version='0.1dev3',
    packages=setuptools.find_namespace_packages(include='*marple.collect*'),
    author='Ensoft Ltd',
    author_email='ensoft@ensoft.co.uk',
    url='https://github.com/ensoft/marple',
    description='',
    package_data={
        'marple.collect': ['tools/*/*'],
    },
    install_requires=[
        'marple.core'
    ]
)

