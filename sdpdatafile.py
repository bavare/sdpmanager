import os.path
import xml.etree.ElementTree as ET
# import simplelogger


class SdpDataFile:
    """ Main class for a single sdpb optimization.

    The inputs for the optimization are given by a single .xml file and the
    output is captured by the corresponding log file.

    The class provides:
    - dict, which returns the contents of the xml tree (without the outer tag)
      as a Python dict
    - sdpbargs, which analyzes the xml file to provide an sdpb argument string:
        - parses known leafs (like <precision>) inside <sdpbParams> to a string
          of sdpb arguments,
        - then adds the content of the leaf <argString> inside <sdpbParams>,
        - then adds the content of the leaf <filename> inside any <sdpFileData>
          tags source files for sdpb, provided <autosdpFiles /> is set.
    - other strings for input sdpb xml files, checkpoint and output files, etc.
    - simple locking/islocked/unlock functionality
    """

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self.logfilename = self.filename + '.log'
        self.xmlfilenames = self.__getxmlfilenames(self._root())
        self.sdpbargs = self.__getsdpbargs(self._root(), self.xmlfilenames)
        self.outfile = self.__getoutfile(self.sdpbargs)
        self.checkpointfile = self.__getcheckpointfile(self.sdpbargs)
        if self.checkpointfile is not None:
            self.backupcheckpointfile = self.checkpointfile + '.bk'
        self.dict = self.__getdictortext(self._root())

    def _tree(self):
        return ET.parse(self.filename)

    def _root(self):
        return self._tree().getroot()

    @staticmethod
    def __getdictortext(tree):
        ret = {}
        for child in tree:
            ret[child.tag] = SdpDataFile.__getdictortext(child)
        if ret == {}:
            ret = tree.text
        return ret

    # # locking: currently implemented via log file.
    # # Touching a (hidden) .lock would also have worked but
    # # afs at CERN does not like having too many files in one dir.
    # def lock(self):
    #     simplelogger.SimpleLogWriter('lck', self.logfilename).write('lock')
    #
    # def unlock(self):
    #     simplelogger.SimpleLogWriter('lck', self.logfilename).write('unlock')
    #
    # def islocked(self):
    #     log = simplelogger.SimpleLogReader(self.logfilename)
    #     return log.lastexprwith(acro='lck') == 'lock'

    # # finished or not: also implemented via log file
    # def setfinished(self):
    #     simplelogger.SimpleLogWriter('fin', self.logfilename).write('done')
    #
    # def isfinished(self):
    #     log = simplelogger.SimpleLogReader(self.logfilename)
    #     return log.lastexprwith(acro='fin', expr='done') == 'done'

    @staticmethod
    def __getxmlfilenames(root):
        xmlfilenames = []
        for child in root.findall('sdpFileData'):
            filename = child.find('filename')
            if filename is not None:
                xmlfilenames.append(filename.text)
        return xmlfilenames

    @staticmethod
    def __getsdpbargs(root, xmlfilenames):
        arglist = []
        sdpbData = root.find('sdpbData')
        if sdpbData is None:
            return arglist
        if sdpbData.find('autosdpFiles') is not None:
            for xmlfilename in xmlfilenames:
                arglist.extend(['--sdpFile', xmlfilename])
        sdpbParams = sdpbData.find('params')
        if sdpbParams is None:
            return arglist
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
            setting = sdpbParams.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting, setting.text])
        sdpbSettingsWithOutArg = ['findPrimalFeasible',
                                  'findDualFeasible',
                                  'detectPrimalFeasibleJump',
                                  'detectDualFeasibleJump',
                                  'noFinalCheckpoint']
        for sdpbSetting in sdpbSettingsWithOutArg:
            setting = sdpbParams.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting])
        sdpbSettingString = sdpbData.find('argString')
        if sdpbSettingString is not None:
            arglist.extend(sdpbSettingString.text.split())
        return arglist

    @staticmethod
    def __getoutfile(args):
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
    def __getcheckpointfile(args):
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
        """ A class to update (sdp) data xml files.

        The xml is supposed to be 'simple', more precisely it has
        - no attributes, and
        - the only meaningful text/tail is in the leafs.
        This form of xml can be captured by Python's 'dict' type, with values
        eiher None, string-representable objects, or dicts themselves.  Such a
        dict should be the argument of updatefile().

        Note this is an update function, so elements in the xml file that do
        not appear in the dict are left untouched.

        The outer tag is not part of this dict. It is commonly called 'sdp' but
        this is ignored.
        """

        def __init__(self, filename):
            self.filename = os.path.abspath(filename)
            # ensure file exists
            if not os.path.isfile(filename):
                with open(self.filename, 'a') as file:
                    file.write('<sdp>\n')
                    file.write('</sdp>\n')

        @staticmethod
        def _updater(xmlel, dict):
            for key, value in dict.items():
                els = xmlel.findall(key)
                if els:
                    el = els[-1]
                else:
                    el = ET.SubElement(xmlel, key)
                if hasattr(value, "items"):
                    SdpDataFileWriter._updater(el, value)
                elif value is None:
                    el.text = ''
                else:
                    el.text = str(value)

        @staticmethod
        def _prettify(xmlel, indent=0):
            lastsubel = None
            for subel in xmlel:
                SdpDataFileWriter._prettify(subel, indent + 2)
                lastsubel = subel
            if lastsubel is not None:
                lastsubel.tail = '\n' + ' ' * indent
                xmlel.text = '\n' + ' ' * (indent + 2)
            xmlel.tail = '\n' + ' ' * indent

        def updatefile(self, dict):
            with open(self.filename, "r+b") as file:
                maintree = ET.parse(file)
                root = maintree.getroot()
                self._updater(root, dict)
                self._prettify(root)
                file.seek(0)
                maintree.write(file)
                file.truncate()
