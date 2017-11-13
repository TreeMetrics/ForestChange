# /usr/bin/env python

# PROJECT:	    EO4Atlantic
# MODULE:		miscellaneous.py
# AUTHOR:		Treemetrics
# DESCRIPTION: 	This contains different methods used in the code

# COPYRIGHT:	(C) 2017 Treemetrics all rights reserved.
# ==========================================================================================

"""
This contains different methods used in the code
"""


import subprocess


def cmd(*args):
    """Run cmd and catch the output (always verbose) """

    if isinstance(args, str):
        args = args.split(',')

    elif isinstance(args, tuple):
        args = list(args)

    cmdstr = ' '.join(args)

    proc = subprocess.Popen([cmdstr], shell=True, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    return out