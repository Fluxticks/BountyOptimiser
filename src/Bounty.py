from util import makeLogger
import logging

class Bounty():

    def __init__(self, itemHash:int, description):
        self._logger = makeLogger('bounty', logging.DEBUG)
        self._itemHash = itemHash
        self._description = description
        self._data = {'weapons':{}}

    def __str__(self):
        return str(self.data)

    @property
    def itemHash(self):
        return self._itemHash

    @property
    def description(self):
        return self._description

    @property
    def data(self):
        return self._data
    
    def addWeapon(self, slots, weapon):
        self._logger.debug('(WEAPON) Adding %s data to slots: %s', weapon, slots)
        if weapon in self._data['weapons']:
            #This shouldn't ever happen but just to ensure it won't go wrong.
            for slot in slots:
                if slot not in self._data['weapons'][weapon]:
                    self._data['weapons'][weapon].add(slot)
        else:
            self._data['weapons'][weapon] = slots

    def addGeneral(self, slots, data):
        self._logger.debug('(GENERAL) Adding %s data to slots: %s', data, slots)
        for slot in slots:
            if slot not in self._data:
                self._data[slot] = data
            else:
                raise IndexError(f'There was already data present in that slot! ({slot})')