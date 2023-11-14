# -*- coding: utf-8 -*-
import codecs
import time
import os
import logging.config
from logging import FileHandler


class SafeFileHandler(FileHandler):
    def __init__(self, filename, mode="a", encoding="utf-8", delay=0, suffix="%Y-%m-%d_%H"):
        if codecs is None:
            encoding = None
        current_time = time.strftime(suffix, time.localtime())
        FileHandler.__init__(self, filename + "." + current_time, mode, encoding, delay)

        self.filename = os.fspath(filename)

        self.mode = mode
        self.encoding = encoding
        self.suffix = suffix
        self.suffix_time = current_time

    def emit(self, record):
        try:
            if self.check_base_filename():
                self.build_base_filename()
            FileHandler.emit(self, record)
        except(KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_base_filename(self):
        time_tuple = time.localtime()

        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                os.path.abspath(self.filename) + '.' + self.suffix_time):
            return 1
        else:
            return 0

    def build_base_filename(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.suffix_time != "":
            index = self.baseFilename.find("." + self.suffix_time)
            if index == -1:
                index = self.baseFilename.rfind(".")
            self.baseFilename = self.baseFilename[:index]

        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = os.path.abspath(self.filename) + "." + self.suffix_time

        if not self.delay:
            self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)


def getLogger(className, level="info"):
    formate = "%(asctime)s -%(levelname)s - %(name)s - %(message)s"
    # formate = "[%(asctime)s] %(levelname)s %(funcName)s [%(process)d]-[%(threadName)s:%(thread)d] [%(name)s:%(lineno)s] %(message)s"
    formatter = logging.Formatter(formate)
    log_path = os.path.join(os.getcwd(), "log")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    tfrHandler = SafeFileHandler(os.path.join(log_path, className + ".log"))
    tfrHandler.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(className)
    logger.addHandler(tfrHandler)
    logger.addHandler(sh)

    if level == 'info':
        logger.setLevel(logging.INFO)
    elif level == 'error':
        logger.setLevel(logging.ERROR)
    return logger
