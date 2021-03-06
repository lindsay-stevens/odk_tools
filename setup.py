from setuptools import setup
from odk_tools import __version__

setup(
    name="odk_tools",
    version=__version__,
    description="Tools for working with ODK XLSForms.",
    url="https://github.com/lindsay-stevens/",
    author="Lindsay Stevens",
    author_email="lindsay.stevens.au@gmail.com",
    packages=['odk_tools'],
    test_suite='tests',
    include_package_data=True,
    license="MIT",
    install_requires=[
        # see requirements.txt
    ],
    keywords="odk",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
)
