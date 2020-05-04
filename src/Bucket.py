from util import makeLogger
import logging

class Bucket:

    def __init__(self, bounty):
        self._logger = makeLogger('bucket', logLevel=logging.DEBUG)
        self._bounties = set()
        self._identifiers = {}
        self.add(bounty)

    @property
    def bounties(self):
        return self._bounties

    def __str__(self):
        return str(self._identifiers)

    def trim(self, bounties):
        
        for bounty in bounties:
            self._bounties.discard(bounty)

    def addWeapon(self, weapon):
        self._logger.debug('Attempting adding weapon components: %s', weapon)
        weaponType = list(weapon.keys())[0]

        slots = []
        foundWeapons = [self._identifiers.get('kinetic'),self._identifiers.get('energy'), self._identifiers.get('power')]

        foundWeapons = list(filter(lambda a: a is not None, foundWeapons))

        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"+str(foundWeapons))

        values = list(weapon.values())[0]

        for value in values:
            if value in self._identifiers:
                if weaponType == self._identifiers[value]:
                    slots.append(value)
                elif foundWeapons.count(self._identifiers.get(value)) > 1:
                    slots.append(value)
                    foundWeapons.remove(self._identifiers.get(value))

            else:
                slots.append(value)

        self._logger.debug('Finished calculating weapons')

        return slots

    def add(self, bounty):
        self._logger.debug('Adding bounty')
        data = bounty.data
        weapons = data.get('weapons')
        slots = []
        if weapons:
            slots = self.addWeapon(weapons)
            if len(slots) == 0:
                self._logger.debug('Unable to add due to conflict with weapons')
                return False

        data.pop('weapons', None)

        valid = True

        for key, value in data.items():
            if not (self._identifiers.get(key) is None or self._identifiers.get(key) == value):
                self._logger.debug('Unable to add due to the following conflict: %s,%s', key, value)
                return False

        if valid:
            self._logger.debug('Valid addition to bucket')
            self._bounties.add(bounty)
            for slot in slots:
                self._identifiers[slot] = list(weapons.keys())[0]
            for key, value in data.items():
                self._identifiers[key] = value

        return valid

    def __len__(self):
        return len(self.bounties)
