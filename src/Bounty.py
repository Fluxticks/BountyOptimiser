class Bounty():

    def __init__(self, itemHash:int, description):
        self._itemHash = itemHash
        self._description = description
        self._data = {}

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
    

    def add(self, keys, value):
        for key in keys:
            if key not in self._data:
                self._data[key] = set()
            self._data[key].add(value)
    