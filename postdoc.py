#!/usr/bin/env python3

import os.path
import sys
import mpmath
import argparse
import sdpdatafile


def analyze(sdpdata):
    if sdpdata.getlogitem('done') is not None:
        return None

    tr = sdpdata.getlogitem('terminateReason')

    if tr is None or \
       tr == 'maxRuntime exceeded' or \
       tr == 'maxIterations exceeded':
        return sdpdata.filename

    if tr == 'maxComplementarity exceeded':
        iP = sdpdata.getdict('sdpbParams').get('initialMatrixScalePrimal')
        if iP is not None:
            newiP = str(mpmath.mpf(iP)/100)
        else:
            newiP = '1e18'
        iD = sdpdata.getdict('sdpbParams').get('initialMatrixScaleDual')
        if iD is not None:
            newiD = str(mpmath.mpf(iD)/100)
        else:
            newiD = '1e18'
        sdpdata.adddict('sdpbParams',
                        {'initialMatrixScalePrimal': newiP},
                        {'initialMatrixScaleDual': newiD},
                        overwrite=True)
        return sdpdata.filename

    if tr == 'primal feasible jump detected' or \
       tr == 'dual feasible jump detected':
        prec = sdpdata.getdict('sdpbParams').get('precision')
        if prec is not None:
            newprec = str(mpmath.mpf(iP * 2))
        else:
            newprec = '800'
        sdpdata.adddict('sdpbParams',
                        {'precision': newprec},
                        overwrite=True)
        return sdpdata.filename

    if tr == 'found primal feasible solution' or \
       tr == 'found dual feasible solution' or \
       tr == 'found primal-dual optimal solution':
        newfilename = None
        if sdpdata.getdict('binarysearch'):
            newfilename = nextbinarysearch(sdpdata)
        elif sdpdata.getdict('maximumsearch'):
            raise NotImplementedError("Maximum search not implemented")
        if newfilename != sdpdata.filename:
            sdpdata.writelog('done', 'done')
        return newfilename

    print('Cannot parse terminateReason in ' + sdpdata.filename + '.',
          file=sys.stderr)
    return None


def addcounter(filename):
    filenameroot, filenamext = os.path.splitext(filename)
    filenamebare, counter = os.path.splitext(filenameroot)
    if counter:
        counter = '.' + str(int(counter.strip('.')) + 1).zfill(3)
    else:
        counter = '.001'
    return filenamebare + counter + filenamext


def nextbinarysearch(sdpdata):
    # todo: create proper copy of tree
    tree = sdpdata._tree()
    root = tree.getroot()
    binsearchdataTree = root.find('binarysearch')
    primal_el = binsearchdataTree.find('primal')
    dual_el = binsearchdataTree.find('dual')
    # update with result
    var = binsearchdataTree.find('varname').text
    for sdpfiledata in root.findall('sdpFileData'):
        current_el = sdpfiledata.find(var)
        if current_el is not None:
            break
    # current_xml =
    current = mpmath.mpf(current_el.text)
    try:
        tr = sdpdata.getlogitem('terminateReason')
    except IndexError:
        tr = None
    if tr == 'found primal feasible solution':
        primal_el.text = str(current)
    elif tr == 'found dual feasible solution':
        dual_el.text = str(current)
    else:
        return None
    # are we done?
    primal = mpmath.mpf(primal_el.text)
    dual = mpmath.mpf(dual_el.text)
    thr = mpmath.mpf(binsearchdataTree.find('threshold').text)
    if abs(primal - dual) < thr:
        return None
    # build new file
    current_el.text = str((primal + dual) / 2)
    sdpfiledata.find('filename').text = \
        addcounter(sdpfiledata.find('filename').text)
    newfilename = addcounter(sdpdata.filename)
    list(map(root.remove, root.findall('log')))
    tree.write(newfilename)
    return newfilename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', metavar='fn', nargs='+',
                        help='a number of sdp data files to analyze')
    parser.add_argument('-r', '--resubmit', action='store_true',
                        help='do not analyze - instead prep for resubmission')
    args = parser.parse_args()
    sdpDataFilenames = args.filenames
    for filename in sdpDataFilenames:
        sdpdata = sdpdatafile.SdpDataFile(filename)
        if args.resubmit:
            sdpdata.adddict('log', {}, append=False)
        else:
            an = analyze(sdpdata)
            if an is not None:
                print(an)
