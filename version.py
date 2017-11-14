#/usr/bin/env python

# PROJECT:	EO4Atlantic
# MODULE:	version.py
# AUTHOR:	(c) Treemetrics
# DESCRIPTION: 	This module prints the current version.

# (C) 2017 Treemetrics All rights reserved.
# ==========================================================================================
"""This module contains the current version number."""

# Important: Version defined according PEP 8 and PEP 386 rules.
# To update version, just change the numbers in the tuple assigned to __version_info__.

__version_info__ = (0, 1, 0)
__version__ = '.'.join(str(x) for x in __version_info__)
__date__ = "31-10-17"
__author__ = 'Treemetrics'
__copyright__ = '(c) Treemetrics 2017. All Rights Reserved'
__license__ = 'Treemetrics 2017 License.'
__credits__ = ''
__history__ = 'See git repository'


