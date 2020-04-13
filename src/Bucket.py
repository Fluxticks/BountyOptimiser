class Bucket():

    def __init__(self, bounty, exclusive):
        self._objectives = []
        self._bounties = []
        self.exclusiveObjectives = exclusive
        self.addBounty(bounty)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return self.toString()

    def toString(self):
        output = {}
        for bounty in self.bounties:
            output[bounty.itemHash] = bounty.objectives
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

        for objective in objectives:
            if objective not in self._objectives:
                self._objectives.append(objective)

    def addBounty(self, bounty):
        bountyObjectives = bounty.objectives

        for tObjective in bountyObjectives:
            for mObjective in self.objectives:
                if self.exclusiveObjectives.get(mObjective) is not None:
                    if tObjective in self.exclusiveObjectives.get(mObjective):
                        return False

        self._bounties.append(bounty)
        self.__addObjectives(bountyObjectives)
        return True

    def addExclusives(self, exclusiveData):

        key = list(exclusiveData.keys())[0]

        if key not in self.exclusiveObjectives:
            self.exclusiveObjectives[key] = exclusiveData.get(key)
            return True
        return False