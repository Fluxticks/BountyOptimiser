class Bounty():

    def __init__(self, itemHash:int, tierData):
        self._itemHash = itemHash
        self._objectives = tierData # {1:objective, 2:objective, ....}

    @property
    def itemHash(self):
        return self._itemHash
    
    @property
    def objectives(self):
        return self._objectives

    @property
    def tier(self):
        try:
            return max(list(self.objectives.keys()))
        except:
            print('oof')
            return -1

    def get(self, key):
        return self.objectives.get(key)

    @property
    def items(self):
        return self.objectives.items()

    @property
    def keys(self):
        return self.objectives.keys()

    @property
    def values(self):
        return self.objectives.values()

    def remove(self,key):
        try:
            del self._objectives[key]
        except:
            pass

    @property
    def list(self):
        data = []
        for key in self.keys:
            data += self.get(key)
        return data

    @property
    def data(self):
        data = {}
        data[self.itemHash] = list(self.values)
        return data

    @property
    def total(self):
        num = 0
        for key in self.objectives.keys():
            num += int(key)
        return num

    def __eq__(self, other):
        if isinstance(other, Bounty):
            return self.total == other.total
        return False

    def __lt__(self, other):
        if isinstance(other, Bounty):
            return self.total < other.total
        return False

    def __gt__(self, other):
        if isinstance(other, Bounty):
            return self.total > other.total
        return False

    def __repr__(self):
        return "ItemHash: "+ str(self.itemHash) + " | Tier: " + str(self.tier) + " | " + str(self.objectives)

    def __len__(self):
        return len(self.keys)

    