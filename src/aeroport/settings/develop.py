"""
Base settings to use when developing aeroport.

How to use it:
--------------

Create your own settings module as python file anywhere in package, gitignore it and ``import *`` from this one.
Then set ``AEROPORT_SETTINGS_MODULE=your_module`` envvar. Your settings then will be used whenever you start
any command.

So that you can override anything you want and not bug with main app codebase.
"""

from aeroport.settings.base import *

DEBUG = True
DEBUG_AUTORELOAD_APP = True
