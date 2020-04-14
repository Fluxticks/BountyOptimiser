from process import Optimise
from api import API
from util import makeColorLog, makeLogger
import logging

if __name__ == '__main__':

    logger = makeLogger('MAIN')
    api = API('731b7c448f4f41fdaaef9d95284d7242')
    manifest = api.manifestUpdate('en')
    logger.info('Manifest is on ver %s', manifest)
    opt = Optimise('731b7c448f4f41fdaaef9d95284d7242', manifest)
    opt.performOptimisation('Fuxticks')