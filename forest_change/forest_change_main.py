# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		forest_change_main.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This module manages the analysis and the outputs.

# COPYRIGHT:	(C) 2018 Treemetrics all rights reserved.
# ==========================================================================================
""" This module manages the analysis and outputs"""

import logging

from core import args_reader
from core import config

from scripts import s2_change

# Check configuration
config.check_config()

# Read args
args = args_reader.main()

if args.module == 'Sentinel2':
    s2_change.main(args)

else:
    logging.exception('Analysis module not found, ' + str(args.module ))
