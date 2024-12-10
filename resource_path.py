import os
import sys

if hasattr(sys, '_MEIPASS'):
    os.environ['RESOURCE_PATH'] = sys._MEIPASS
else:
    os.environ['RESOURCE_PATH'] = os.path.abspath(".")
