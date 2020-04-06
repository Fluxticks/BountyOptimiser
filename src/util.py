import logging
import colorlog
from coloured_log import ColoredFormatter

def makeColorLog(logName, logLevel = logging.INFO):
    LOG_LEVEL = logLevel
    LOGFORMAT = '  %(name)s : %(log_color)s%(levelname)-8s%(reset)s | %(message)s (%(filename)s:%(lineno)d)'
    stream = colorlog.StreamHandler()
    stream.setFormatter(colorlog.ColoredFormatter(LOGFORMAT))

    file = logging.FileHandler(logName.lower()+'.log')
    file.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file.setFormatter(file_format)

    logger = logging.getLogger(logName.upper())
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    logger.addHandler(file)

    return logger

def makeLogger(logName, logLevel = logging.INFO):
    LOG_LEVEL = logLevel
    LOGFORMAT = '[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)'
    #LOGFORMAT = '  [%(name)s][%(levelname)-8s] | %(message)s (%(filename)s:%(lineno)d)'
    formatter = ColoredFormatter(LOGFORMAT)

    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)

    file = logging.FileHandler(logName.lower()+'.log')
    file.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file.setFormatter(file_format)

    logger = logging.getLogger(logName.upper())
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    logger.addHandler(file)

    return logger

def unHashToId(hashvalue):
    val = int(hashvalue)
    if (val & (1 << (32 -1))) != 0:
        val = val - (1 << 32)
    return val