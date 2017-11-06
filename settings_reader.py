# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		settings_reader.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module read and manage settings.

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================
""" This module read and manage settings."""

import json


def read_file(filepath):
    with open(filepath) as data_file:
        return json.load(data_file)