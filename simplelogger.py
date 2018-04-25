import os.path


class SimpleLogWriter:

    def __init__(self, acro, filename):
        self.filename = os.path.abspath(filename)
        self.acro = acro
        if not os.path.isfile(filename):
            open(filename, 'a').close()
        self.fp = None

    # allows 'with' but is not used because the cern world is a weird world
    def __enter__(self):
        self.fp = open(self.filename, 'a', 1)
        return self

    # see previous comment
    def __exit__(self, type, value, traceback):
        self.fp.close()
        self.fp = None

    def write(self, expr, bonusexpr=None):
        if self.fp is not None:
            self._writep(expr, bonusexpr)
        else:
            self.__enter__()
            try:
                self._writep(expr, bonusexpr)
            finally:
                self.__exit__(None, None, None)

    def _writep(self, expr, bonusexpr=None):
        self.fp.write(self.acro + ' :: ' + str(expr))
        if bonusexpr is not None:
            self.fp.write(' :: ' + str(bonusexpr))
        self.fp.write('\n')


class SimpleLogReader:

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        # ensure file exists to make other functions work
        if not os.path.isfile(filename):
            open(filename, 'a').close()

    def entries(self):
        with open(self.filename, 'r') as f:
            for line in list(f):
                yield line.rstrip().split(' :: ')

    def reversedentries(self):
        return iter(reversed(list(self.entries())))

    def numlineswith(self, acro=None, expr=None, bonusexpr=None):
        i = 0
        for line in self.entries():
            if self._match(line, acro, expr, bonusexpr):
                i += 1
        return i

    def lastlinewith(self, acro=None, expr=None, bonusexpr=None):
        for line in self.reversedentries():
            if self._match(line, acro, expr, bonusexpr):
                return line

    def lastexprwith(self, acro=None, expr=None, bonusexpr=None):
        lastline = self.lastlinewith(acro, expr, bonusexpr)
        if lastline is not None:
            return lastline[1]

    def lastbonusexprwith(self, acro=None, expr=None, bonusexpr=None):
        lastline = self.lastlinewith(acro, expr, bonusexpr)
        if lastline is not None:
            return lastline[2]

    @staticmethod
    def _match(line, acro=None, expr=None, bonusexpr=None):
        if acro is not None:
            if acro != line[0]:
                return False
        if expr is not None:
            if len(line) < 2:
                return False
            elif line[1] != expr:
                return False
        if bonusexpr is not None:
            if len(line) < 3:
                return False
            elif line[2] != bonusexpr:
                return False
        return True
