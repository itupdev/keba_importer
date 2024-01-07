# -*- coding: utf-8 -*-
"""Initialize"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
__lib_path__ = os.path.dirname(os.path.realpath(__file__))

