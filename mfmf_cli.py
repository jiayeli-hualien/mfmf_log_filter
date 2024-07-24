#!/bin/python

from pathlib import Path
import sys
import os
import typing
import argparse
import logging
import csv
import re
from io import TextIOWrapper
from types import CodeType


class FilterArgs:
    # store arguments from the user
    logFolderPath: Path
    cfgDirPath: Path
    patternCfgFilePath: Path
    allowListCfgFilePath: Path
    blockListCfgFilePath: Path
    isAdvancedExecScriptEnabled: bool

    def __init__(self, args) -> None:
        self.logFolderPath = Path(args.logFolderPath)
        self.cfgDirPath = Path(args.configDirPath)
        self.patternCfgFilePath = Path(
            self.cfgDirPath) / Path('pattern_config.csv')
        self.allowListCfgFilePath = Path(
            self.cfgDirPath) / Path('allowed_file_list.csv')
        self.blockListCfgFilePath = Path(
            self.cfgDirPath) / Path('blocked_file_list.csv')
        self.isAdvancedExecScriptEnabled = args.exec_script


STR_TRUE = "true"
STR_FALSE = "false"


class FileBasenameMatcher:
    regexpList: list[re.Pattern]
    settingList: list[dict]

    def __init__(self, csvFilePath: Path):
        self.regexpList = list()
        self.settingList = list()
        self.initLists(csvFilePath)

    def initLists(self, csvFilePath: Path):
        logging.debug("reading csv file {}".format(csvFilePath))
        if not csvFilePath.is_file():
            logging.warning("text file {} is not exist, use empty list".format(
                str(csvFilePath)))
            return

        with open(csvFilePath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                logging.debug("row {}".format(row))
                if row["rule_enable"] != STR_TRUE:
                    logging.debug(
                        "this row disabled, skip row name '{}'".format(
                            row["rule_name"]))
                    continue
                case_flag = 0
                if row["is_case_senstive"] == STR_FALSE:
                    case_flag = re.IGNORECASE
                # TODO: regexp checker in GUI
                pattern = re.compile(row["file_basename_regexp"], case_flag)
                logging.debug("pattern of row {}".format(pattern))
                self.regexpList.append(pattern)
                self.settingList.append(row)

    def match(
            self,
            basename) -> tuple[bool, int]:  # is matched, index of mached rule
        for idx, pattern in enumerate(self.regexpList):
            if pattern.match(basename):
                return idx
        return None

    def log(self):
        for i in range(len(self.regexpList)):
            logging.info("regexp[{}] = {}".format(i, self.regexpList[i]))
        return


class ExecProgram:
    isEnable: bool
    program: CodeType
    script: str

    def __init__(self, script: str, isEnable):
        self.isEnable = isEnable
        self.program = None
        if isEnable:
            self.program = compile(script, "<string>", "exec")
        self.script = script

    def runAndJudge(self, match: re.Match) -> bool:
        if not self.isEnable:  # Don't filter out
            return True

        retLocalVar = {"result": False}
        arguments = {"groups": match.groups(), "groupdict": match.groupdict()}
        logging.debug("Exec for program '{}', arguments '{}''".format(
            self.script, arguments))

        exec(self.program, arguments, retLocalVar)

        # True / False
        logging.debug(
            "Exec for program '{}', groups '{}', groupdict '{}', return '{}'".
            format(self.script, match.groups(), match.groupdict(),
                   bool(retLocalVar["result"])))
        return bool(retLocalVar["result"])


class TextLogLineFilter:
    regexpList: list[re.Pattern]
    execProgramList: list[ExecProgram]
    settingList: list[dict]

    def __init__(self, csvFilePath: Path):
        self.regexpList = list()
        self.settingList = list()
        self.execProgramList = list()
        self.initLists(csvFilePath)

    def initLists(self, csvFilePath: Path):
        if not csvFilePath.is_file():
            logging.warning("file '{}' is not exist, use empty list")
            return
        with open(csvFilePath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                logging.debug("read row {}", row)
                if row["pattern_enable"] != STR_TRUE:
                    logging.debug(
                        "pattern with name {} is not enabled, skip append",
                        row["pattern_name"])
                    continue
                # store setting
                self.settingList.append(row)
                case_flag = 0
                if row["is_case_senstive"] == STR_FALSE:
                    case_flag = re.IGNORECASE
                pattern = re.compile(row["regexp_pattern"], case_flag)
                # handle regexp
                self.regexpList.append(pattern)

                # handle advanced exec scripts
                execEnable = False
                if row["exec_filter_enable"] == STR_TRUE:
                    execEnable = True
                execProgram = ExecProgram(row["exec_filter_script"],
                                          execEnable)
                self.execProgramList.append(execProgram)

    def search(self, textLogLine: str, argExecScriptEnable: bool):
        # return first match rule
        for idx, pattern in enumerate(self.regexpList):
            retSearch = pattern.search(textLogLine)
            if retSearch == None:
                continue
            if argExecScriptEnable:
                if not self.execProgramList[idx].runAndJudge(retSearch):
                    continue
            return idx
        return None


class MfMfCtx:
    # store long-term stages of the filter
    arg: FilterArgs
    blockedFileListPattern: FileBasenameMatcher
    allowedFileListPattern: FileBasenameMatcher
    textLogLineFilter: TextLogLineFilter
    output: TextIOWrapper

    def __init__(self, arg) -> None:
        self.arg = arg

    def setBlockedFileListPattern(self, pattern):
        self.blockedFileListPattern = pattern

    def setAllowedFileListPattern(self, pattern):
        self.allowedFileListPattern = pattern

    def setTextLogLineFilter(self, lineFilter: TextLogLineFilter):
        self.textLogLineFilter = lineFilter

    def setOutput(self, output):
        self.output = output


class CuiArgParser:

    def __init__(self) -> None:
        pass

    def parse(self, argv: list[str]) -> FilterArgs:
        argParser = argparse.ArgumentParser(
            description=
            "MFMF CUI - Multi file multil filter log filter's command line user interface"
        )
        argParser.add_argument('-l',
                               '--logFolderPath',
                               type=str,
                               required=True,
                               help='Log Folder to parse')
        argParser.add_argument('-c',
                               '--configDirPath',
                               type=str,
                               required=True,
                               help='A folder has whole config files')
        argParser.add_argument('-p',
                               '--preprocessorPlugin',
                               type=str,
                               required=False,
                               help='Preprocessor plugin python file')
        argParser.add_argument(
            '-e',
            '--exec_script',
            action='store_true',
            required=False,
            help=
            'DANGER turn on exec script support, default off. (Danger: May allow arbitrary script execution from pattern_config.csv)'
        )
        args = argParser.parse_args()
        logging.debug('args = {}'.format(args))
        return args


def initLogging():
    logging.basicConfig(
        filename='mfmf_logging.txt',
        filemode='w',
        level=logging.DEBUG,
        format=
        '%(asctime)s - %(name)s - {%(pathname)s:%(lineno)4d} - %(levelname)s - %(message)s'
    )


class MFMFfilter:
    ctx: MfMfCtx = None

    def __init__(self, ctx: MfMfCtx):
        self.ctx = ctx

    def preprocess(slef):
        # TODO preprocessor to unzip or others by plugin
        pass

    def filter(self):
        # Traverse all files
        blockedFilePatterns = self.ctx.blockedFileListPattern
        allowedFilePatterns = self.ctx.allowedFileListPattern
        for subTreeRoot, dirs, files in os.walk(self.ctx.arg.logFolderPath):
            for filename in files:
                logging.debug("os.walk() to file {}".format(filename))
                ret = blockedFilePatterns.match(filename)
                if ret:
                    logging.debug("{} {}".format(ret[0], ret[1]))
                if blockedFilePatterns.match(filename) != None:
                    logging.debug(
                        "file blocked, skip read file {}".format(filename))
                    continue
                if allowedFilePatterns.match(filename) == None:
                    logging.debug(
                        "file not matched in allowd list, skip read file {}".
                        format(filename))
                    continue

                logging.debug(
                    "start parsing file '{}' ......".format(filename))
                logFilePath = Path(subTreeRoot) / Path(filename)
                output: TextIOWrapper = self.ctx.output
                dictList = self.filterWithDiffEncodings(logFilePath)
                for outdict in dictList:
                    output.write("{}\n".format(outdict))

    def filterWithDiffEncodings(self, logFilePath: Path):
        try:
            dictList = self.filterLogFile(logFilePath, None)
            return dictList
        except UnicodeDecodeError as eEncode:
            logging.error(
                "Error occurs when parsing file: {}".format(logFilePath))
            logging.error("Exception: '{}'".format(eEncode))

        logging.warning(
            "Try latin-1 encoding on file {}, may output non-ANSI chars wrong".
            format(logFilePath))

        # TODO: study when 'latin-1' work when got a corrupted utf-8 file.
        try:
            dictList = self.filterLogFile(logFilePath, 'latin-1')
            return dictList
        except UnicodeDecodeError as eEncode:
            logging.error(
                "Still error with encoding 'latin-1' when parsing file: {}".
                format(logFilePath))
            logging.error("Exception: '{}'".format(eEncode))

        return list()

    def filterLogFile(self, logFilePath: Path, myEncoding):
        logLineFilter: TextLogLineFilter = self.ctx.textLogLineFilter
        execScriptEanble = self.ctx.arg.isAdvancedExecScriptEnabled
        retDict = list()
        with open(logFilePath, mode="r", encoding=myEncoding) as file:
            for line in file:
                line = line.strip()
                ret = logLineFilter.search(line, execScriptEanble)
                if ret == None:
                    continue
                outdict = {
                    "log_filepath": logFilePath,
                    "text_line": line,
                    "first_match_pattern_id": ret
                }
                retDict.append(outdict)
        return retDict


def main(argv: list[str]):
    initLogging()

    cuiArgParser = CuiArgParser()
    filterArgs = FilterArgs(cuiArgParser.parse(argv))

    ctx = MfMfCtx(filterArgs)
    blockListPattern = FileBasenameMatcher(filterArgs.blockListCfgFilePath)
    ctx.setBlockedFileListPattern(blockListPattern)
    allowListPattern = FileBasenameMatcher(filterArgs.allowListCfgFilePath)
    ctx.setAllowedFileListPattern(allowListPattern)

    logging.info("BlockList:")
    ctx.blockedFileListPattern.log()
    logging.info("AllowList:")
    ctx.allowedFileListPattern.log()

    lineFilter = TextLogLineFilter(filterArgs.patternCfgFilePath)
    ctx.setTextLogLineFilter(lineFilter)

    # TODO: get output file path from arg
    ctx.setOutput(sys.stdout)
    mfmfFilter = MFMFfilter(ctx)

    mfmfFilter.filter()


if __name__ == '__main__':
    main(sys.argv)
