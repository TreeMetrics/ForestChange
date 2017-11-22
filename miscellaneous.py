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

import sys
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


def dict_find(key, dictionary):
    """ Find recursively item in dict"""

    for k, v in dictionary.iteritems():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in dict_find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in dict_find(key, d):
                    yield result


# def chunks(l, n):
#     n = max(1, n)
#     return (l[i:i+n] for i in xrange(0, len(l), n))


def chunks(l, size, maxsize=sys.maxsize):
    """Yield successive n-sized chunks from l."""

    maxsize=536870912

    #if n == None:
    #    if not size == None:
    n = size/maxsize/2
    n = max(1, n)

    for i in xrange(0, len(l), n):
        yield l[i:i + n]
