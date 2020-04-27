class Bounty():

    def __init__(self, itemHash:int, description:str):
        self._itemHash = itemHash
        self._description = description

    @property
    def itemHash(self):
        return self._itemHash
    
    @property
    def description(self):
        return self._description
    