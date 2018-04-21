#!/usr/bin/env python3

import argparse
import simplelogger


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('expression', help='expression to match')
    parser.add_argument('filenames', metavar='fn', nargs='+',
                        help='a number of sdp data files to analyze')
    parser.add_argument('-a', '--acronym',
                        help="""Show only message with matching acro.""")
    parser.add_argument('-snf', '--nofilename', action='store_true',
                        help="""Do not print filename""")
    args = parser.parse_args()
    sdpDataFilenames = args.filenames
    maxlen = max(map(len, sdpDataFilenames))
    for filename in sdpDataFilenames:
        log = simplelogger.SimpleLogReader(filename)
        val = log.lastlinewith(acro=args.acronym, expression=args.expression)
        if val is None:
            val = ""
        if args.nofilename:
            print(val)
        else:
            print(filename.ljust(maxlen) + ': ' + val)
