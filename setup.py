from setuptools import setup, find_packages

setup(
    name='ppycron',
    version='0.0.5',
    packages=find_packages(),
    url='https://github.com/marciobbj/ppycron',
    install_requires=[
        "attrs==21.4.0",
        "black==22.3.0",
        "click==8.1.3",
        "iniconfig==1.1.1",
        "mypy-extensions==0.4.3",
        "packaging==21.3",
        "pathspec==0.9.0",
        "platformdirs==2.5.2",
        "pluggy==1.0.0",
        "py==1.11.0",
        "pyparsing==3.0.8",
        "pytest",
        "pytest-mock",
        "tomli==2.0.1",
        "typing_extensions==4.2.0",
    ],
    license='MIT License',
    author='Marcio Bernardes Barbosa Junior',
    author_email='marciobernardes@live.com',
    description='PPyCron lets you manage crontabs in Linux based systems.'
)
