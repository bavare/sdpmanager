#!/usr/bin/env python3

import argparse
import sdpdatafile


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('entry', help='dictionary entry to output')
    parser.add_argument('filenames', metavar='fn', nargs='+',
                        help='a number of sdp data files to analyze')
    parser.add_argument('-d', '--dictionary',
                        help="""Choice of a dictionary to select the entry from,
                                defaults to 'log'.""", default='log')
    parser.add_argument('-nf', '--nofilename', action='store_true',
                        help="""Do not print filename""")
    args = parser.parse_args()
    sdpDataFilenames = args.filenames
    maxlen = max(map(len, sdpDataFilenames))
    for filename in sdpDataFilenames:
        sdpdata = sdpdatafile.SdpDataFile(filename)
        val = sdpdata.getdict(args.dictionary).get(args.entry)
        if val is None:
            val = ""
        if args.nofilename:
            print(val)
        else:
            print(filename.ljust(maxlen) + ': ' + val)
