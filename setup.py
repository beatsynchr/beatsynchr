from setuptools import setup, find_packages

setup(
    name='beatsynchr',
    version='0.1.0',
    description='Generate beat-synced slideshows from images and audio',
    author='Jakub Nurkiewicz',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    entry_points={
        'console_scripts': [
            'beatsynchr=beatsynchr.core:generate_slideshow',
        ],
    },
)
