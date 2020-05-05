from util import makeLogger
import logging

logger = makeLogger('bounty', logging.INFO)

class Bounty():

    def __init__(self, itemHash: int, description, title):
        #logger = makeLogger('bounty', logging.INFO)
        self._itemHash = itemHash
        self._description = description
        self._title = title
        self._data = {'weapons': {}}

    def __str__(self):
        return str(self.data)

    @property
    def itemHash(self):
        return self._itemHash

    @property
    def description(self):
        return self._description

    @property
    def title(self):
        return self._title

    @property
    def data(self):
        return self._data

    def addWeapon(self, slots, weapon):
        logger.debug('(WEAPON) Adding %s data to slots: %s', weapon, slots)
        if weapon in self._data['weapons']:
            # This shouldn't ever happen but just to ensure it won't go wrong.
            for slot in slots:
                if slot not in self._data['weapons'][weapon]:
                    logger.warn('This shouldn\'t have happened: weapon (%s), slot (%s)', weapon, slot)
                    self._data['weapons'][weapon].add(slot)
        else:
            self._data['weapons'][weapon] = slots

    def addGeneral(self, slots, data):
        logger.debug('(GENERAL) Adding %s data to slots: %s', data, slots)
        for slot in slots:
            if slot not in self._data:
                self._data[slot] = [data]
            else:
                self._data[slot].append(data)
                # raise IndexError(f'There was already data present in that slot! ({slot})')
