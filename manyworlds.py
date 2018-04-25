import subprocess as sp
import os
import shutil


class World:
    sdpfilecreator = 'echo'
    sdpb = 'echo'
    submitter = 'echo'

    def createSdpFiles(self, sdpdata, options=None):
        return sp.run([self.sdpfilecreator, sdpdata.filename],
                      encoding='ascii', check=True)

    def runSdpb(self, sdpdata, options=None):
        return sp.run([self.sdpb] + sdpdata.sdpbargs, stderr=sp.PIPE,
                      encoding='ascii', check=True)

    def submit(self, sdpdata, options=None):
        return sp.run([self.submitter, sdpdata.filename], stderr=sp.PIPE,
                      encoding='ascii', check=True)

    def waitforcompletion(self, sdpdata):
        pass

    def warmup(self, sdpdata):
        pass

    def cooldown(self, sdpdata):
        pass

    @staticmethod
    def movefile(origfile, destfile, log=None):
        if os.path.isfile(origfile):
            shutil.move(origfile, destfile)
            logmsg = 'Moved ' + origfile + ' to ' + destfile + '.'
        else:
            logmsg = 'Could not find ' + origfile + ' to move.'
        if log is not None:
            log.write(logmsg)
        else:
            print(logmsg)

    @staticmethod
    def copyfile(origfile, destfile, log=None):
        if os.path.isfile(origfile):
            shutil.copyfile(origfile, destfile)
            logmsg = 'Copied ' + origfile + ' to ' + destfile + '.'
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
            logmsg = 'Removed ' + origfile + '.'
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
    else:
        # default
        return World()
