import os
import shutil
import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install


def additional_setup():
    '''
    crypted-cookie-monster does ship some small autocpmpletion scripts that will be installed
    by this function. The corresponding scripts are written to the home directory of the user
    who installs the package and affect the following files:

        ~/.bash_completion
        ~/.bash_completion.d/ccm
        ~/.zsh/_ccm

    Parameters:
         None

     Returns:
         None
    '''
    user_home = os.path.expanduser("~")
    module_path = os.path.abspath(os.path.dirname(__file__))

    #creating a .bash_completion.d directory
    config_dir = "/.bash_completion.d/"
    if not os.path.isdir(user_home + config_dir):
        os.makedirs(user_home + config_dir, exist_ok=True)

    #creating a .bash_completion file
    config_file = "/.bash_completion"
    if not os.path.isfile(user_home + config_file):
        shutil.copy(module_path + "/ccm/resources/bash_completion", user_home + config_file)

    #creating bash autocomplete script
    config_file = config_dir + "ccm"
    shutil.copy(module_path + "/ccm/resources/bash_completion.d/ccm", user_home + config_file)

    #creating a .zsh directory
    #config_dir = "/.zsh/"
    #if not os.path.isdir(user_home + config_dir):
    #    os.makedirs(user_home + config_dir, exist_ok=True)

    ##creating zsh autocomplete script
    #config_file = config_dir + "_ccm"
    #shutil.copy(module_path + "/ccm/resources/zsh_completion.d/_ccm", user_home + config_file)


class PostDevelopCommand(develop):
    '''
    Simple hook to create the necessary directory structure atfer devlopment install

    Parameters:
         develop                 (Unkown)                Some argument provided by setup.py
 
    Returns:
         None
    '''
    def run(self):
        additional_setup()
        develop.run(self)


class PostInstallCommand(install):
    '''
    Simple hook to create the necessary directory structure atfer install

    Parameters:
         install                 (Unkown)                Some argument provided by setup.py

    Returns:
         None
    '''
    def run(self):
        additional_setup()
        install.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()
    setuptools.setup(
        name="ccm",
        version="1.0.0",
        author="Tobias Neitzel (qtc)",
        author_email="",
        description="ccm - A small python library that helps identify vulnerabilities inside of encrypted data.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        packages=setuptools.find_packages(),
        package_data = {
            'ccm': [
                'resources/bash_completion.d/*',
                #'resources/zsh_completion.d/*',
                ]},


        scripts=[
                'bin/ccm',
                ],

        cmdclass={
            'develop': PostDevelopCommand,
            'install': PostInstallCommand,
        },

        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: Unix",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        ],
    )
