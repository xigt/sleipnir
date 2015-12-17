#!/usr/bin/env python

import os
import argparse
import logging

from xigt.codecs import xigtxml
from sleipnir import dbi

def run(args):
    for f in args.files:
        logging.info('Adding %s to database.' % f)
        xc = xigtxml.load(f)
        name = os.path.splitext(os.path.basename(f))[0]
        dbi.add_corpus(xc, name=name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='Increase the verbosity (can be repeated: -vvv).')
    # parser.add_argument('dbdir', help='Database directory')
    parser.add_argument('files', nargs='*', help='files to add to the db')
    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))
    run(args)

