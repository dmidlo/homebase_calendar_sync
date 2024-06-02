from setuptools import setup, find_packages

from setuptools import setup, find_packages

setup(
    name='homebase_calendar_sync',
    version='0.1.7',
    author='David Midlo',
    author_email='dmidlo@gmail.com',
    description='A simple web scraper that reads gethomebase.com\'s schedule and updates Google Calendar.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dmidlo/homebase_calendar_sync',  # Update this to your project's URL
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=open('requirements.txt').read().splitlines(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'homebase_calendar_sync=homebase_calendar_sync.homebase_calendar_sync:main',
        ],
    },
)