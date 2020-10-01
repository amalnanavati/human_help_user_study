import datetime

class Logger(object):
    def __init__(self, logDir="outputs/", filename="log.txt"):
        self.f = open(logDir+filename, "a")
        self.datetimeFormatStr = "{:%b %d, %Y %Z %H:%M:%S:%f}"
        beginningStr = """
********************************************************************************
[{}] BEGIN LOGGING
********************************************************************************
""".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        #print(beginningStr)
        self.f.write(beginningStr)

        self.timesSinceLastFlush = 0
        self.flushEveryNTimes = 3000 # roughly once every two minutes when there is one user playing the tutorial/game

    def logPrint(self, *args, printToOutput=False, **kwargs):
        self.timesSinceLastFlush += 1
        headerStr = "[{}] ".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        self.f.write(headerStr)
        for argument in args:
            self.f.write(str(argument))
            self.f.write(", ")
        self.f.write("\n")

        if (self.timesSinceLastFlush >= self.flushEveryNTimes):
            self.f.flush()
            os.fsync(self.f.fileno())
            self.timesSinceLastFlush = 0
            print("Cleared logfile buffer")

        if (printToOutput):
            printArgs = [headerStr, *args]
            print(*printArgs, **kwargs)

    def logRaiseException(self, *args, **kwargs):
        self.timesSinceLastFlush += 1
        headerStr = "[{}] ".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        self.f.write(headerStr)
        for argument in args:
            self.f.write(str(argument))
            self.f.write(", ")
        self.f.write("\n")

        if (self.timesSinceLastFlush >= self.flushEveryNTimes):
            self.f.flush()
            os.fsync(self.f.fileno())
            self.timesSinceLastFlush = 0
            print("Cleared logfile buffer")

        printArgs = [headerStr, *args]
        raise Exception(*printArgs, **kwargs)

    def close(self):
        endingStr = """
********************************************************************************
[{}] END LOGGING
********************************************************************************
""".format(self.datetimeFormatStr.format(datetime.datetime.now()))
        print(endingStr)
        self.f.write(endingStr)
        self.f.close()
