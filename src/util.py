import logging
import colorlog
from coloured_log import ColoredFormatter

DEBUG_TRACE_NUM = 9
def trace(self, message, *args, **kws):
    if self.isEnabledFor(DEBUG_TRACE_NUM):
        self._log(DEBUG_TRACE_NUM, message, args, **kws)
logging.Logger.trace = trace
logging.addLevelName(9, 'TRACE')

def makeLogger(logName, logLevel=logging.INFO):
    LOG_LEVEL = logLevel
    LOGFORMAT = '[%(name)s][%(levelname)s] | %(message)s (%(filename)s:%(lineno)d)'
    #LOGFORMAT = '  [%(name)s][%(levelname)-8s] | %(message)s (%(filename)s:%(lineno)d)'
    formatter = ColoredFormatter(LOGFORMAT)

    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)

    file = logging.FileHandler(logName.lower()+'.log')
    file.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file.setFormatter(file_format)

    logger = logging.getLogger(logName.upper())
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    logger.addHandler(file)

    return logger

def makeColorLog(logName, logLevel=logging.INFO):
    LOG_LEVEL = logLevel
    LOGFORMAT = '  %(name)s : %(log_color)s%(levelname)-8s%(reset)s | %(message)s (%(filename)s:%(lineno)d)'
    stream = colorlog.StreamHandler()
    stream.setFormatter(colorlog.ColoredFormatter(LOGFORMAT))

    file = logging.FileHandler(logName.lower()+'.log')
    file.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file.setFormatter(file_format)

    logger = logging.getLogger(logName.upper())
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    logger.addHandler(file)

    return logger

def unHashToId(hashvalue):
    val = int(hashvalue)
    if (val & (1 << 31)) != 0:
        val = val - (1 << 32)
    return val

class bcolours:
    """The ANSI colour codes
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def dprint(data, parent='data', level=0):
    """Prints a dictionary with formatting
    
    Args:
        data (dict): The dictionary to be printed
        parent (str, optional): The key from the parent for nested dictionaries
        level (int, optional): How many nested dictionaries in the recursion is
    """
    tabs = '\t' * level
    cprint('{}' + tabs + parent + '{}: ', bcolours.OKBLUE)
    tabs = '\t' * (level + 1)
    for key, value in data.items():
        if isinstance(value, dict):
            dprint(value, parent=key, level=level + 1)
        elif isinstance(value, list):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.WARNING, value, bcolours.ENDC)
        elif isinstance(value, int):
            cprint('{}' + tabs + key + '{}: {}{}{}', bcolours.ERROR, bcolours.OKGREEN, value, bcolours.ENDC)
        elif isinstance(value, str):
            cprint('{}' + tabs + key + '{}: {}', bcolours.ERROR, value)


def cprint(text, colour, *args):
    """Prints a message with colour
    
    Args:
        text (str): The text to be coloured
        colour (bcolours.COLOR): The colour of the text
        *args: Any extra strings to be printed
    """
    print(text.format(colour, bcolours.ENDC, *args))
    return text.format(colour, bcolours.ENDC, *args) + '\n'