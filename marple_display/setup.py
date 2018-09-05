import setuptools

setuptools.setup(
    name='marple.display',
    version='0.1dev3',
    packages=setuptools.find_namespace_packages(include='*marple.display*'),
    author='Ensoft Ltd',
    author_email='ensoft@ensoft.co.uk',
    url='https://github.com/ensoft/marple',
    description='',
    package_data={
        'marple.display': ['tools/*/*'],
    },
    install_requires=[
        'marple.core',
        'ipython>=6.5.0',
        'ipython-genutils>=0.2.0',
        'matplotlib>=2.2.2',
        'numpy>=1.13.3',
        'pandas>=0.23.4',
        'PyQt5>=5.11.2',
        'PyQt5-sip>=4.19.12',
        'pyqtgraph>=0.10.0',
        'scipy>=0.19.1',
    ]
)

