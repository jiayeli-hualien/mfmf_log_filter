#!/bin/python

from pathlib import Path
import sys
import typing
import argparse
import logging

class FilterArgs:
    logFolderPath = None
    cfgDirPath = None
    patternCfgFilePath = None
    allowListCfgFilePath = None
    blockListCfgFilePath = None

    def __init__(self, args) -> None:
        self.logFolderPath = args.logFolderPath
        self.cfgDirPath = args.configDirPath
        self.patternCfgFilePath = Path(self.cfgDirPath) / Path('pattern_config.csv')
        self.allowListCfgFilePath = Path(self.cfgDirPath) / Path('allow_file_list.csv')
        self.blockListCfgFilePath = Path(self.cfgDirPath) / Path('block_file_list.csv')

class MfMfCtx:
    arg = None

    def __init__(self, arg) -> None:
        self.arg = arg

class CuiArgParser:
    def __init__(self) -> None:
        pass

    def parse(self, argv: list[str]) -> FilterArgs:
        argParser = argparse.ArgumentParser(
            description="MFMF CUI - Multi file multil filter log filter's command line user interface")
        argParser.add_argument('-l', '--logFolderPath', type=str, required=True, help='Log Folder to parse')
        argParser.add_argument('-c', '--configDirPath', type=str, required=True, help='A folder has whole config files')
        argParser.add_argument('-p', '--preprocessorPlugin', type=str, required=False, help='Preprocessor plugin python file')
        args = argParser.parse_args()
        logging.debug('args = {}'.format(args))
        return args

def initLogging():
    logging.basicConfig(filename='mfmf_logging.txt',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main(argv: list[str]):
    initLogging()
    cuiArgParser = CuiArgParser()
    filterArgs = FilterArgs(cuiArgParser.parse(argv))
    ctx = MfMfCtx(filterArgs)


if __name__ == '__main__':
    main(sys.argv)
