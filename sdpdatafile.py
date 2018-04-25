import os.path
import xml.etree.ElementTree as ET
import simplelogger


class SdpDataFile:

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self.logfilename = self.filename + '.log'
        self.xmlfilenames = self.__setxmlfilenames(self._root())
        self.sdpbargs = self.__setsdpbargs(self._root(), self.xmlfilenames)
        self.outfile = self.__setoutfile(self.sdpbargs)
        self.checkpointfile = self.__setcheckpointfile(self.sdpbargs)
        if self.checkpointfile is not None:
            self.backupcheckpointfile = self.checkpointfile + '.bk'

    def _tree(self):
        return ET.parse(self.filename)

    def _root(self):
        return self._tree().getroot()

    def getdict(self, tag):
        trees = self._root().findall(tag)
        if not trees:
            return {}
        dict = {}
        tree = trees[-1]
        for child in tree:
            dict[child.tag] = child.text
        return dict

    # locking: currently implemented via log file.
    # Touching a (hidden) .lock would also have worked but
    # afs at CERN does not like having too many files in one dir.
    def lock(self):
        simplelogger.SimpleLogWriter('lck', self.logfilename).write('lock')

    def unlock(self):
        simplelogger.SimpleLogWriter('lck', self.logfilename).write('unlock')

    def islocked(self):
        log = simplelogger.SimpleLogReader(self.logfilename)
        return log.lastexprwith(acro='lck') == 'lock'

    # finished or not: also implemented via log file
    def setfinished(self):
        simplelogger.SimpleLogWriter('fin', self.logfilename).write('done')

    def isfinished(self):
        log = simplelogger.SimpleLogReader(self.logfilename)
        return log.lastexprwith(acro='fin', expr='done') == 'done'

    @staticmethod
    def __setxmlfilenames(root):
        xmlfilenames = []
        for child in root.findall('sdpFileData'):
            # TODO: add error messages if no filename exist
            filename = child.find('filename')
            if filename is None:
                raise Exception("Found 'sdpFiledata' without \
                                attribute 'filename'.")
            else:
                xmlfilenames.append(filename.text)
        return xmlfilenames

    @staticmethod
    def __setsdpbargs(root, xmlfilenames):
        sdpbParamsTree = root.find('sdpbParams')
        if sdpbParamsTree is None:
            return None
        arglist = []
        for xmlfilename in xmlfilenames:
            arglist.extend(['--sdpFile', xmlfilename])
        sdpbSettingsWithArg = ['sdpFile',
                               'paramFile',
                               'outFile',
                               'checkpointFile',
                               'precision',
                               'maxThreads',
                               'checkpointInterval',
                               'maxIterations',
                               'maxRuntime',
                               'dualityGapThreshold',
                               'primalErrorThreshold',
                               'dualErrorThreshold',
                               'initialMatrixScalePrimal',
                               'initialMatrixScaleDual',
                               'feasibleCenteringParameter',
                               'infeasibleCenteringParameter',
                               'stepLengthReduction',
                               'choleskyStabilizeThreshold',
                               'maxComplementarity']
        for sdpbSetting in sdpbSettingsWithArg:
            setting = sdpbParamsTree.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting, setting.text])
        sdpbSettingsWithOutArg = ['findPrimalFeasible',
                                  'findDualFeasible',
                                  'detectPrimalFeasibleJump',
                                  'detectDualFeasibleJump',
                                  'noFinalCheckpoint']
        for sdpbSetting in sdpbSettingsWithOutArg:
            setting = sdpbParamsTree.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting])
        sdpbSettingString = sdpbParamsTree.find('argString')
        if sdpbSettingString is not None:
            arglist.extend(sdpbSettingString.text.split())
        return arglist

    @staticmethod
    def __setoutfile(args):
        if args is None:
            return None
        for i in range(len(args)):
            if args[i] == '--outFile' or args[i] == '-o':
                return args[i + 1]
        else:
            for i in range(len(args)):
                if args[i] == '--sdpFile' or args[i] == '-s':
                    return os.path.splitext(args[i + 1])[0] + '.out'

    @staticmethod
    def __setcheckpointfile(args):
        if args is None:
            return None
        for i in range(len(args)):
            if args[i] == '--checkpointFile' or args[i] == '-c':
                return args[i + 1]
        else:
            for i in range(len(args)):
                if args[i] == '--sdpFile' or args[i] == '-s':
                    return os.path.splitext(args[i + 1])[0] + '.ck'


class SdpDataFileWriter:

        def __init__(self, filename):
            self.filename = os.path.abspath(filename)

        def update(self, tag, dict, overwrite=True):
            with open(self.filename, "r+b") as file:
                maintree = ET.parse(file)
                root = maintree.getroot()
                trees = root.findall(tag)
                tree = None
                if trees:
                    tree = trees[-1]
                else:
                    tree = ET.SubElement(root, tag)
                    tree.text = '\n'
                    tree.tail = '\n'
                for key, value in dict.items():
                    els = tree.findall(key)
                    if els and overwrite:
                        el = els[-1]
                    else:
                        el = ET.SubElement(tree, key)
                    if value:
                        el.text = value
                    else:
                        el.text = '\n'
                    el.tail = '\n'
                file.seek(0)
                maintree.write(file)
                file.truncate()
