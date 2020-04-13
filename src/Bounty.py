class Bounty():

    def __init__(self, itemHash:int, objectives:list):
        self._itemHash = itemHash
        self._objectives = objectives

    @property
    def itemHash(self):
        return self._itemHash
    
    @property
    def objectives(self):
        return self._objectives
    