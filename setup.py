# -*- coding: utf-8 -*-
"""
Created on Wed May 16 10:53:53 2018

@author: tjbanks
"""

from cx_Freeze import setup, Executable

base = None    

executables = [Executable("100Cell.py", base=base)]

packages = ["idna","re","subprocess","threading","tempfile","shutil","os","tkinter"]
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "<any name>",
    options = options,
    version = "<any number>",
    description = '<any description>',
    executables = executables
)