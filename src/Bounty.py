class Bounty():

    def __init__(self, itemHash:int, objectives:list):
        self._itemHash = itemHash
        self._objectives = objectives
        self._relatedBounty = None

    @property
    def itemHash(self):
        return self._itemHash
    
    @property
    def objectives(self):
        return self._objectives

    @property
    def relatedBounty(self):
        return self._relatedBounty
    
    @relatedBounty.setter
    def relatedBounty(self, bounty):
        self._relatedBounty = bounty
    