from api import API
from enums import ComponentTypeEnum, StatsEnum, ItemCategoryEnum, BucketEnum, CategoryEnum
from util import makeColorLog, makeLogger, unHashToId, dprint
import logging
import sqlite3
import json
import re
from itertools import chain

from Bucket import Bucket
from Bounty import Bounty

logger = makeColorLog('Optimiser', logLevel=logging.INFO)

class Optimise():

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest
        logger.debug('Manifest loc: %s', self._manifestLoc)
        self.makeBuckets()

    def makeBuckets(self):
        
        self.weaponBuckets = ['auto rifle', 'scout rifle', 'hand cannon', 'sniper', 'sidearm', 'pulse rifle', 'submachine gun', 'shotgun', 'fusion rifle', 'trace rifle', 'grenade launcher', 'rocket launcher', 'linear fusion rifle', 'sword', 'heavy machine gun', 'ability']
        self.enemyBuckets = ['fallen', 'vex', 'hive', 'taken', 'scorn', 'cabal', 'guardians'] #
        self.enemyWording = ['opponents', 'combatants', 'enemies', 'any target'] #
        self.elementBuckets = ['solar', 'void', 'arc'] #
        self.slotBuckets = ['kinetic', 'energy', 'power']
        self.killBuckets = ['rapid', 'precision', 'multi'] #
        self.abilityBuckets = ['melee', 'super', 'grenade']
        self.planetBuckets = ['edz', 'titan', 'moon', 'nessus', 'tangled shore', 'dreaming city', 'mercury', ' io', 'mars']

        #Mutually Exclusive buckets mean the objective in the same bucket can't happen at the same time
        exclusiveBuckets = [self.weaponBuckets, self.enemyBuckets, self.elementBuckets, self.slotBuckets, self.abilityBuckets, self.planetBuckets]

        self.xorBuckets = [self.weaponBuckets, self.abilityBuckets]

        self.exclusiveData = {}

        for bucket in exclusiveBuckets:
            self.exclusiveData.update(self.makeExclusive(bucket))

        self.exclusiveData['kinetic'] += self.elementBuckets

        #dprint(self.exclusiveData)

        self.baseBuckets = self.weaponBuckets + self.enemyBuckets + self.enemyWording + self.elementBuckets + self.slotBuckets + self.killBuckets + self.abilityBuckets + self.planetBuckets


    def makeExclusive(self, items):
        data = {}
        for i in range(len(items)):
            data[items[i]] = items[:i] + items[i+1:]
        return data


    def getGeneralBuckets(self, objective):

        buckets = []
        objective = objective.lower()

        for bucket in self.baseBuckets:
            if bucket in objective:
                buckets.append(bucket)

        if 'generate orbs' in objective or 'orbs created' in objective:
            if 'super' not in buckets:
                buckets.append('orbs')

        if 'collect orbs' in objective or 'orbs collected' in objective:
            buckets.append('masterwork')

        return buckets


    def getCrucibleBuckets(self, objective):
        
        crucibleBuckets = ['win', 'crucible', 'matches']
        modesBuckets = ['clash', 'control', 'rumble', 'skirmish', 'supremacy', 'breakthrough', 'countdown', 'survival', 'iron banner']
        objectiveBasedBuckets = {'supremacy':'crests', 'control':'zones', 'countdown':'charges'}

        objective = objective.lower()

        buckets = self.getGeneralBuckets(objective)

        for bucket in crucibleBuckets:
            if bucket in objective:
                buckets.append('crucible')
                break

        for bucket in modesBuckets:
            if bucket in objective:
                buckets.append(bucket)

        for mode,bucket in objectiveBasedBuckets.items():
            if bucket in objective:
                if mode not in buckets:
                    buckets.append(mode)

        return buckets


    def getGambitBuckets(self, objective):

        gambitBuckets = ['gambit', 'win', 'matches']
        objectiveBasedBuckets = ['motes']
        objective = objective.lower()

        buckets = self.getGeneralBuckets(objective)

        for bucket in gambitBuckets:
            if bucket in objective:
                buckets.append('gambit')
                break

        for bucket in objectiveBasedBuckets:
            if bucket in objective:
                buckets.append(bucket)

        return buckets


    def getLocationBuckets(self, objective):

        locationBuckets = ['chests', 'gather']

        objective = objective.lower()

        buckets = self.getGeneralBuckets(objective)

        for bucket in locationBuckets:
            if bucket in objective:
                buckets.append(bucket)

        if 'patrols' in objective:
            for planet in self.planetBuckets:
                if planet in objective and planet not in buckets:
                    buckets.append(planet)
                    break

        return buckets


    def findCommonBuckets(self, activity):
        
        bucketsMade = []

        '''first = list(activity.keys())[0]

        firstData = activity.get(first)

        firstBounty = Bounty(first, firstData)

        bucket = Bucket(firstBounty, self.exclusiveData)
        bucketsMade.append(bucket)
        del activity[first]'''

        for itemHash, objectives in activity.items():
            foundValidBucket = False
            bounty = Bounty(itemHash, objectives)
            for bucket in bucketsMade:
                foundValidBucket = bucket.addBounty(bounty)      
            if not foundValidBucket:
                bucket = Bucket(bounty, self.exclusiveData)
                bucketsMade.append(bucket)
            bucketsMade.sort(key=lambda x: x.size, reverse=False)

        return bucketsMade
        
    def performOptimisation(self, player):
        profile = self.getPlayerData(player)

        playerId = profile[1]
        playerType = profile[0]

        items = self.getAllItems(playerType, playerId)

        characters = self.getCharacters(playerType, playerId)

        bounties = self.getBounties(items, characters)
        weapons = self.getWeapons(items, characters)

        activityFiltered = self.filterCharacters(bounties)

        crucible = self.findKeyObjectiveData(activityFiltered.get('2305843009301295844').get('crucible'), self.getCrucibleBuckets)
        gambit = self.findKeyObjectiveData(activityFiltered.get('2305843009301295844').get('gambit'), self.getGambitBuckets)
        locations = self.findKeyObjectiveData(activityFiltered.get('2305843009301295844').get('locations'), self.getLocationBuckets)
        other = self.findKeyObjectiveData(activityFiltered.get('2305843009301295844').get('other'), self.getGeneralBuckets)

        logger.info('Crucible objectives: %s', crucible)
        logger.info('Gambit objectives: %s', gambit)
        logger.info('Locations objectives: %s', locations)
        logger.info('Other objectives: %s', other)

        common = self.findCommonBuckets(other)

        logger.info('Common buckets: %s', common)


    def getAllItems(self, membershipType, membershipId):
        response = self._api.getProfileInventory(membershipType, membershipId)
        logger.debug('Got response for GetInventory call: %s', response)

        return response


    def getBounties(self, items, characterIds):
        characterInventories = items.get('characterInventories').get('data')

        bounties = {}

        for character in characterIds:
            bounties[character] = []
            for item in characterInventories.get(character).get('items'):
                if item.get('bucketHash') == BucketEnum.QUESTS and item.get('expirationDate') is not None:
                    itemDefinition = self.getValueFromTable(unHashToId(item.get('itemHash')), 'DestinyInventoryItemDefinition')
                    if CategoryEnum.QUEST_STEP not in itemDefinition.get('itemCategoryHashes'):
                        item['manifest'] = itemDefinition
                        bounties[character].append(item)
                        logger.debug('Appended hashed item for character %s : %s', character, item.get('itemHash'))

        logger.debug('Bounty data: %s', bounties)
        logger.info('Done finding bounties for all characters (%d)', len(characterIds))
        return bounties


    def getWeapons(self, items, characterIds):
        weaponHashes = [BucketEnum.KINETIC_WEAPONS, BucketEnum.ENERGY_WEAPONS, BucketEnum.POWER_WEAPONS]
        characterInventories = items.get('characterInventories').get('data')
        vaultInventory = items.get('profileInventory').get('data').get('items')
        items = []

        for character in characterIds:
            for item in characterInventories.get(character).get('items'):
                if item.get('bucketHash') in weaponHashes:
                    items.append(item)

        for item in vaultInventory:
            if item.get('bucketHash') == BucketEnum.VAULT:
                manifestItem = self.getValueFromTable(unHashToId(item.get('itemHash')), 'DestinyInventoryItemDefinition')
                if manifestItem.get('inventory').get('bucketTypeHash') in weaponHashes:
                    item['bucketHash'] = manifestItem.get('inventory').get('bucketTypeHash')
                    items.append(item)
                    logger.debug('Appended hased item from vault: %s', item.get('itemHash'))

        logger.debug('Weapons data: %s', items)
        logger.info("Done finding weapons for all characters (%d) and Vault", len(characterIds))
        return items

        
    def getCharacters(self, membershipType, membershipId):
        response = self._api.getProfile(membershipType, membershipId)
        characters = response.get('profile').get('data').get('characterIds')
        
        return characters


    def getPlayerData(self, player):
        response = self._api.getPlayer(player)

        pId = response.get('membershipId')
        pType = response.get('membershipType')
        displayName = response.get('displayName')

        return [pType, pId, displayName]


    def filterCharacters(self, bounties:dict):
        characters = list(bounties.keys())

        filtered = {}

        for character in characters:
            filtered[character] = self.filter(bounties.get(character))

        return filtered


    def filter(self, items:list):

        activities = {'crucible':[], 'gambit':[],'strikes':[], 'locations':[], 'other':[]}

        logger.debug('Filtering items: %s', items)

        for item in items:
            itemHash = item.get('itemHash')
            itemInstance = item.get('itemInstanceId')
            itemStore = [itemHash, itemInstance]
            itemData = self.getValueFromTable(unHashToId(itemHash), 'DestinyInventoryItemDefinition')
            stackId = itemData.get('inventory').get('stackUniqueLabel')

            if 'crucible' in stackId or 'pvp' in stackId:
                activities['crucible'].append(itemStore)
            elif 'gambit' in stackId:
                activities['gambit'].append(itemStore)
            elif 'v400.bounties.destinations' in stackId:
                activities['locations'].append(itemStore)
            else:
                activities['other'].append(itemStore)

            logger.debug('Sorted bounty: %s', item)

        logger.debug('Filtered items: %s', activities)
        logger.info('Done filtering items')
        return activities


    def sortByLocation(self, locations:dict):

        planets = {}

        for item, objectives in locations.items():
            planet = objectives[-1]
            if planet in planets:
                planets[planet] += objectives[:-1]
            else:
                planets[planet] = objectives[:-1]

        return planets


    def findKeyObjectiveData(self, bounties:list, optimalMethod):

        bountyObjectives = {}

        for bounty in bounties:
            itemHash = bounty[0]
            itemData = self.getValueFromTable(unHashToId(itemHash), 'DestinyInventoryItemDefinition')
            objectiveHashes = itemData.get('objectives').get('objectiveHashes')
            bountyObjectives[itemHash] = []
            for objective in objectiveHashes:
                #objectiveData = self.getValueFromTable(unHashToId(objective), 'DestinyObjectiveDefinition')
                #logger.debug('From Objective Data buckets gained: %s', self.getBucketForObjective(objectiveData.get('progressDescription')))
                objectiveBucket = optimalMethod(itemData.get('displayProperties').get('description'))
                logger.debug('From Item Data buckets gained: %s', objectiveBucket)
                bountyObjectives[itemHash].append(objectiveBucket)
            
            bountyObjectives[itemHash] = list(chain.from_iterable(bountyObjectives.get(itemHash)))

        return bountyObjectives


    def getValueFromTable(self, valueId, tableName):
        if 'Destiny' not in tableName:
            tableName = 'Destiny' + tableName
        if 'Definition' not in tableName:
            tableName += 'Definition'
        try:
            conn = sqlite3.connect(self._manifestLoc)
            cursor = conn.cursor()
            statement = f'SELECT json FROM {tableName} WHERE id = {valueId}'
            logger.debug('Searching manifest with statement: %s', statement)
            cursor.execute(statement)
            data = cursor.fetchone()
            conn.close()
            #Removes the tuple anmd gives the data as str
            data = data[0]
            #Turn data str into dict for easier access
            data = json.loads(data)
            return data
        except OSError as oserror:
            logger.error('An OS error occured: %s', oserror)
        except sqlite3.DatabaseError as dberror:
            logger.error('A DataBase Error occured while trying to access the manifest file: %s', dberror)
        except sqlite3.Error as generic:
            logger.error('A Generic Error occured while trying to access the manifest file: %s', generic)