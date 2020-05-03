class Bucket():

    def __init__(self, bounty):
        self._bounties = [bounty]
        self._identifiers = {}
        self.add(bounty)

    def addWeapon(self, weapon):
        weaponType = list(weapon.keys())[0]

        slots = []

        for value in weapon.values():
            if value in self._identifiers:
                if weaponType == self._identifiers[value]:
                    slots.append(value)
            else:
                slots.append(value)

        return slots

    def add(self, bounty):
        data = bounty.data
        weapons = data.get('weapons')

        if weapons is not None:
            slots = self.addWeapon(weapons)
            if len(slots) == 0:
                return False

        data.pop('weapons', None)

        valid = True

        for key,value in data:
            if not (self._identifiers.get(key) is None or self._identifiers.get(key) == value):
                valid = False

        if valid:
            for slot in slots:
                    self._identifiers[slot] = list(weapons.keys())[0]
            for key,value in data:
                self._identifiers[key] = value

        return valid