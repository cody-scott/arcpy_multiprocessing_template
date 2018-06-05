import os

import arcview
import arcpy

from utils.multiprocessing_helpers import set_multi_exec

# region Arc Specific
# This is for getting the manager working right and sending right python
import sys
if not hasattr(sys, 'argv'):
    sys.argv  = ['']
# endregion

def main():
    set_multi_exec()

