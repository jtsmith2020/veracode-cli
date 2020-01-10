from setuptools import setup, find_packages

setup(
    name="veracode-cli",
    version="2019.10.1",
    packages=find_packages(),
    license="MIT",
    author="John Smith",
    url="https://github.com/jtsmith2020/veracode-cli",
    author_email="jtsmith@veracode.com",
    description="A rich CLI for interacting with Veracode services",
    install_requires=[
        "requests >= 2.18.4",
        "pytz >= 2018.4",
    ],
    entry_points={
        "console_scripts": ["veracode-cli = veracode.veracode:start"]
    }
)