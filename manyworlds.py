import subprocess as sp
import os
import shutil


class World:
    """
    Template class for a world (a cluster) providing methods for:
    - submitting and managing jobs:
        - submit
        - isreallyrunning (which is supposed to check in with the cluster)
        - waitforcompletion (which is supposed to check in with the cluster)
    - running a job on a node:
        - warmup
        - createSdpFiles
        - runSdpb
        - cooldown
    In a barebones world it suffices to set the three executables below.
    """
    sdpfilecreator = 'echo'
    sdpb = 'echo'
    submitter = 'echo'

    def submit(self, sdpdata, options=None):
        return sp.run([self.submitter, sdpdata.filename], stderr=sp.PIPE,
                      encoding='ascii', check=True)

    def isreallyrunning(self, submissionid):
        pass

    def waitforcompletion(self, submissionid):
        pass

    def warmup(self, sdpdata, log=None):
        pass

    def cooldown(self, sdpdata, tr, log=None):
        pass

    def createSdpFiles(self, sdpdata, options=None):
        return sp.run(self.sdpfilecreator + ' ' + sdpdata.filename,
                      encoding='ascii', check=True, shell=True)

    def runSdpb(self, sdpdata, options=None):
        return sp.run([self.sdpb] + sdpdata.sdpbargs,
                      encoding='ascii', check=True)

    @staticmethod
    def checkorcreatedir(dest, log=None):
        """
        Check that a file can be written to 'dest', which can be
        either a directory or a filename.
        """
        destdir = os.path.dirname(dest)
        if  destdir != "":
            if not os.path.exists(destdir):
                os.makedirs(destdir)
                if log is not None:
                    log.write('Created destination ' + destdir + '.')
                else:
                    print('Created destination ' + destdir + '.')


    @staticmethod
    def movefile(origfile, dest, log=None):
        if os.path.isfile(origfile):
            World.checkorcreatedir(dest, log)
            shutil.move(origfile, dest)
            logmsg = 'Moved ' + origfile + ' to ' + dest + '.'
        else:
            logmsg = 'Could not find ' + origfile + ' to move.'
        if log is not None:
            log.write(logmsg)
        else:
            print(logmsg)

    @staticmethod
    def copyfile(origfile, dest, log=None):
        """
        Copy a file to dest, which can be either a file or a directory.
        """
        if os.path.isfile(origfile):
            World.checkorcreatedir(dest, log)
            shutil.copy(origfile, dest)
            logmsg = 'Copied ' + origfile + ' to ' + dest + '.'
        else:
            logmsg = 'Could not find ' + origfile + ' to copy.'
        if log is not None:
            log.write(logmsg)
        else:
            print(logmsg)

    @staticmethod
    def removefile(origfile, log=None):
        if os.path.isfile(origfile):
            os.remove(origfile)
            logmsg = 'Removed: ' + origfile
        else:
            logmsg = 'Could not find ' + origfile + ' to remove.'
        if log is not None:
            log.write(logmsg)
        else:
            print(logmsg)


def getworld(arg):
    if arg == 'cern':
        import cernworld
        return cernworld.CernWorld()
    elif arg == 'local':
        import localworld
        return localworld.LocalWorld()
    elif arg == 'fake':
        import fakeworld
        return fakeworld.FakeWorld()
    else:
        # default
        return World()
