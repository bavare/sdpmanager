import subprocess as sp
import os
import manyworlds
import htcondor as htc


class CernWorld(manyworlds.World):
    bindir = '/afs/cern.ch/user/v/vanrees/bin/'
    libdir = '/afs/cern.ch/user/v/vanrees/local/lib'
    afsdir = '/afs/cern.ch/work/v/vanrees/temp/'
    sdpfilecreator = bindir + 'qftinads-exe'
    sdpb = bindir + 'sdpb'

    def __init__(self):
        pass

    @staticmethod
    def _hide(filename):
        path, file = os.path.split(filename)
        return os.path.join(path, '.' + file)

    def warmup(self, sdpdata, log=None):
        cerndict = sdpdata.dict.get('cernworld')
        transferdict = cerndict.get('filetransfer')
        if transferdict is None:
            return
        origdir = transferdict.get('origdestdir')
        if origdir is None:
            origdir = self.afsdir
        files = sdpdata.xmlfilenames + [sdpdata.outfile,
                                        sdpdata.checkpointfile,
                                        sdpdata.backupcheckpointfile]
        for file in files:
            origfile = origdir + os.path.basename(file)
            self.copyfile(origfile, file, log)

    def cooldown(self, sdpdata, tr, log=None):
        cerndict = sdpdata.dict.get('cernworld')
        transferdict = cerndict.get('filetransfer')
        if transferdict is None:
            return
        if 'onlyontimeout' in transferdict and \
           tr != 'maxRuntime exceeded' and \
           tr != 'maxIterations exceeded':
            return
        destdir = transferdict.get('origdestdir')
        files = sdpdata.xmlfilenames + [sdpdata.outfile,
                                        sdpdata.checkpointfile,
                                        sdpdata.backupcheckpointfile]
        if destdir is None:
            destdir = self.afsdir
        for file in files:
            destfile = destdir + os.path.basename(file)
            self.copyfile(file, destfile, log)

    def createSdpFiles(self, sdpdata, options=None):
        cerndict = sdpdata.dict.get('cernworld')
        executabledict = cerndict.get('executables')
        if 'sdpcreator' in executabledict:
            self.sdpfilecreator = executabledict.get('sdpcreator')
        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = \
            self.libdir + ":" + my_env["LD_LIBRARY_PATH"]
        return sp.run([self.sdpfilecreator, sdpdata.filename],
                      encoding='ascii', check=True, env=my_env)

    def runSdpb(self, sdpdata, options=None):
        cerndict = sdpdata.dict.get('cernworld')
        executabledict = cerndict.get('executables')
        if 'sdpb' in executabledict:
            self.sdpb = executabledict.get('sdpb')
        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = \
            self.libdir + ":" + my_env["LD_LIBRARY_PATH"]
        sp.run([self.sdpb] + sdpdata.sdpbargs,
               stderr=sp.STDOUT,
               check=True,         # i.e. raise an exception when sdpb fails
               encoding='ascii',   # may need upgrading for sdpb-unicode
               env=my_env)
    # Code below should log sdpb output to the log file but maybe
    # caused the "shadow exceptions" I experienced at the CERN cluster.
    # with simplelogger.SimpleLogWriter('sdp', sdpdata.logfilename) as log:
    #     my_env = os.environ.copy()
    #     my_env["LD_LIBRARY_PATH"] = \
    #         self.libdir + ":" + my_env["LD_LIBRARY_PATH"]
    #     sdpbproc = sp.Popen([self.sdpb] + sdpdata.sdpbargs, stdout=sp.PIPE,
    #                         stderr=sp.STDOUT, encoding='ascii', env=my_env)
    #     for line in iter(sdpbproc.stdout.readline, ''):
    #         log.write(line.rstrip())

    def submit(self, sdpdata, options=None):
        submissiondict = {"executable": self.bindir + "clusterstarter.sh",
                          "arguments": self.bindir +
                          "worker.py -w cern " +
                          sdpdata.filename,
                          "log": self._hide(sdpdata.filename + '.condorlog'),
                          "output": self._hide(sdpdata.filename + '.out'),
                          # str(sdpdata.numlogs()).zfill(3),
                          "error": self._hide(sdpdata.filename + '.err')
                          # str(sdpdata.numlogs()).zfill(3)}
                          }
        sdpdict = sdpdata.dict.get('cernworld').get('cluster')
        if sdpdict is not None:
            # add "+" because that's what htcondor can stomach
            if sdpdict.get('MaxRuntime'):
                sdpdict['+MaxRuntime'] = sdpdict['MaxRuntime']
                del sdpdict['MaxRuntime']
            submissiondict.update(sdpdict)
        op = sp.check_output(['condor_submit', '-terse'],
                             input=str(htc.Submit(submissiondict)),
                             encoding='utf-8')
        # expected output: XXXXX.0 - XXXXX.0 with XXXXX the submissionid
        return op.split()[0].split('.')[0]
        # alternative submission code below:
        # coll = htc.Collector()
        # schedd_ad = coll.locate(htc.DaemonTypes.Schedd)
        # self.schedd = htc.Schedd(schedd_ad)
        # with self.schedd.transaction() as txn:
        #     submissionid = str(sub.queue(txn))
        #     return submissionid
        # this alternaitve should work according to docs, but does not:
        # submitted jobs get held because log file cannot be created.
        # Interestingly, the problem disappears after using condor_submit once.
        # (perhaps an authentication error?)

    def getlogfilename(self, submissionid):
        coll = htc.Collector()
        schedd = htc.Schedd(coll.locate(htc.DaemonTypes.Schedd))
        it = schedd.xquery(requirements='ClusterId =?= ' + submissionid,
                           projection=['UserLog'])
        logfilename = None
        for i in it:
            logfilename = i['UserLog']
            assert(os.path.isfile(logfilename))
            break
        return logfilename

    def waitforcompletion(self, submissionid):
        logfilename = self.getlogfilename(submissionid)
        if logfilename is not None:
            sp.run(['condor_wait', logfilename, submissionid])

    def isreallyrunning(self, submissionid):
        coll = htc.Collector()
        schedd = htc.Schedd(coll.locate(htc.DaemonTypes.Schedd))
        it = schedd.xquery(requirements='ClusterId =?= ' + submissionid,
                           projection=['JobStatus'])
        # 0	Unexpanded
        # 1	Idle
        # 2	Running
        # 3	Removed
        # 4	Completed
        # 5	Held
        # 6	Submission_err
        for i in it:
            if i['JobStatus'] == 1 or i['JobStatus'] == 2:
                return True
        return False
        # logfilename = self.getlogfilename(submissionid)
        # print(logfilename)
        # op = sp.check_output(['condor_wait', '-wait', '-1', '-status',
        #                       logfilename, submissionid], encoding='utf-8')
        # print(op)
