from util import makeLogger
import logging


logger = makeLogger('bucket', logLevel=logging.INFO)


class Bucket:

    def __init__(self, bounty):
        #logger = makeLogger('bucket', logLevel=logging.DEBUG)
        self._bounties = set()
        self._identifiers = {}
        self.add(bounty)

    @property
    def bounties(self):
        return self._bounties

    def __str__(self):
        return str(self._identifiers)

    @property
    def identifiers(self):
        return self._identifiers

    def trim(self, bounties):

        for bounty in bounties:
            self._bounties.discard(bounty)

    def addWeapon(self, weapon):

        weaponType = list(weapon.keys())[0]

        slots = []
        foundWeapons = [self._identifiers.get('kinetic'), self._identifiers.get('energy'),
                        self._identifiers.get('power')]

        foundWeapons = list(filter(lambda a: a is not None, foundWeapons))

        logger.debug('Found weapons: %s', foundWeapons)
        logger.debug('Attempting adding weapon components: %s', weapon)

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

        logger.debug('Finished calculating weapons: %s', slots)

        return slots

    def addActivity(self, activities):
        logger.debug('Attempting to add activities: %s', activities)

        if self._identifiers.get('activity') is None:
            return activities

        overlap = []

        for activity in activities:
            if activity in self._identifiers.get('activity'):
                overlap.append(activity)

        return overlap

    def add(self, bounty):
        logger.trace('Adding bounty')
        data = bounty.data
        weapons = data.get('weapons')
        slots = []
        if weapons:
            slots = self.addWeapon(weapons)
            if len(slots) == 0:
                logger.debug('Unable to add due to conflict with weapons')
                return False

        activity = data.get('activity')
        overlap = None
        if activity:
            overlap = self.addActivity(activity)
            if len(overlap) == 0:
                logger.debug('Unable to add due to conflict of activities')
                return False

        data.pop('weapons', None)
        data.pop('activity', None)

        for key, value in data.items():
            if not (self._identifiers.get(key) is None or self._identifiers.get(key) == value):
                logger.debug('Unable to add due to the following conflict: %s,%s', key, value)
                return False

        logger.trace('Valid addition to bucket')
        self._bounties.add(bounty)
        for slot in slots:
            self._identifiers[slot] = list(weapons.keys())[0]
        if overlap is not None:
            self._identifiers['activity'] = overlap
        for key, value in data.items():
            self._identifiers[key] = value

        return True

    def __len__(self):
        return len(self.bounties)
