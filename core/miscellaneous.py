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

import os
import sys
import subprocess
import logging


def is_float(input):

    try:
        num = float(input)

    except ValueError:
        return False

    return True


def cmd(*args):
    """Run cmd and catch the output (always verbose) """

    if isinstance(args, str):
        args = args.split(',')

    elif isinstance(args, tuple):
        args = list(args)

    cmdstr = ' '.join(args)
    logging.debug(cmdstr)

    proc = subprocess.Popen([cmdstr], shell=True, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()

    if out:
        logging.debug(out)

    if err:
        logging.error(err)

    return out


def new_unique_file(file_path, overwrite=False):
    """Force to create a folder or file with unique name."""

    if os.path.exists(file_path):
        if overwrite:
            os.remove(file_path)

        else:
            n = 0
            while os.path.exists(file_path):
                n += 1
                # file_path = os.path.splitext(file_path)[0] + '_' + str(n) + os.path.splitext(file_path)[1]

                file_path = str(os.path.splitext(file_path)[0]).split("__")[0] + '__' + str(n) + \
                            os.path.splitext(file_path)[1]

    return file_path


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


def is_number(s):

    if s:
        try:
            float(s)
            return True
        except ValueError:
            return False
    else:
        return False