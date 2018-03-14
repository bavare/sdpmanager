import sdpdatafile
import shutil
import os.path


def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


def clone(sdpdata, newfilename, updatedict):
    shutil.copyfile(sdpdata.filename, newfilename)
    newsdpdata = sdpdatafile.SdpDataFile(newfilename)
    for tag, valdict in updatedict.items():
        newsdpdata.adddict(tag, valdict, overwrite=True)


sdpdata = sdpdatafile.SdpDataFile('newtestrun/base.xml')
h1list = frange(0.1, 1, 0.1)

for it, h1 in enumerate(h1list):
    f, e = os.path.splitext(sdpdata.filename)
    newfilename = f + '_' + str(it) + e
    newsdpbfilename = os.path.basename(f + '_' + str(it) + '_sdpb' + e)
    clone(sdpdata,
          newfilename,
          {'sdpFileData': {'h1': str(h1), 'filename': newsdpbfilename}})
