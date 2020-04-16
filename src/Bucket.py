from copy import deepcopy

class Bucket():

    def __init__(self, bounty, exclusive):
        self._objectives = {}
        self._bounties = []
        self.exclusiveObjectives = exclusive
        self.addBounty(bounty)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def toString(self):
        output = []
        for bounty in self.bounties:
            output.append(bounty.data)
        return str(output)


    @property
    def bounties(self):
        return self._bounties

    @property
    def objectives(self):
        return self._objectives

    @property
    def size(self):
        return len(self.bounties)


    def __addObjectives(self, objectives):

        for key,objective in objectives.items():
            if not self._objectives.get(key):
                self._objectives[key] = []
            if objective not in self._objectives.get(key):
                self._objectives[key].append(objective)

    def addBounty(self, bounty):
        maxTier = bounty.tier

        for selfBounty in self.bounties:
            if not self.__doChecks(selfBounty, bounty):
                return False

        self._bounties.append(bounty)
        self.__addObjectives(bounty.objectives)

        return True
       

    def __doChecks(self, currentBounty, bounty):

        copyCurrentBounty = deepcopy(currentBounty)
        copyBounty = deepcopy(bounty)

        if copyCurrentBounty.tier == copyBounty.tier:
            tier = copyBounty.tier
            if not any(x in copyCurrentBounty.get(tier) for x in copyBounty.get(tier)):
                return False
        else:
            if copyCurrentBounty > copyBounty:
                copyCurrentBounty.remove(copyCurrentBounty.tier)
            else:
                copyBounty.remove(copyBounty.tier)

        for key in copyCurrentBounty.keys:
            if copyBounty.get(key):
                if not any(x in copyCurrentBounty.get(key) for x in copyBounty.get(key)):
                    return False

        return True



    def addExclusives(self, exclusiveData):

        key = list(exclusiveData.keys())[0]

        if key not in self.exclusiveObjectives:
            self.exclusiveObjectives[key] = exclusiveData.get(key)
            return True
        return False