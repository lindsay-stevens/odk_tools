from setuptools import setup, find_packages

setup(
    name="odk_tools",
    version="0.0.7",
    description="Tools for working with ODK XLSforms.",
    url="https://github.com/lindsay-stevens/",
    author="Lindsay Stevens",
    author_email="lindsay.stevens.au@gmail.com",
    packages=find_packages(),
    test_suite='tests',
    include_package_data=True,
    license="MIT",
    install_requires=[
        'python-docx>=0.8.5', 'xlrd>=0.9.4',
        'Pillow>=3.0.0', 'lxml>=3.5.0',
        'pyxform'
        #'https://github.com/XLSForm/pyxform/archive/e33e260b3ae532dabbda9c9843b0f525da67d001.zip'
    ],
    keywords="odk",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
)
