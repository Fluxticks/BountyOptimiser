from process import Optimise
from api import API
from util import makeColorLog, makeLogger
from Exceptions import DiscordError

if __name__ == '__main__':

    logger = makeLogger('MAIN')
    api = API('731b7c448f4f41fdaaef9d95284d7242')
    manifest = api.manifestUpdate('en')
    logger.info('Manifest is on ver %s', manifest)
    opt = Optimise('731b7c448f4f41fdaaef9d95284d7242', manifest)
    try:
        opt.performOptimisation('Bowsers Enabled')
    except DiscordError as e:
        logger.error('Discord Error: %s', e.message)

def setup():
    logger = makeLogger('MAIN')
    api = API('731b7c448f4f41fdaaef9d95284d7242')
    manifest = api.manifestUpdate('en')
    logger.info('Manifest is on ver %s', manifest)
    opt = Optimise('731b7c448f4f41fdaaef9d95284d7242', manifest)
    return opt
