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
        
        weapons = ['auto rifle', 'scout rifle', 'hand cannon', 'sniper', 'sidearm', 'pulse rifle', 'submachine gun', 'shotgun', 'fusion rifle', 'trace rifle', 'grenade launcher', 'rocket launcher', 'linear fusion rifle', 'sword', 'heavy machine gun']
        combatants = ['fallen', 'vex', 'hive', 'taken', 'scorn', 'cabal', 'guardians'] 
        targets = ['opponents', 'combatants', 'enemies', 'any target'] 
        elements = ['solar', 'void', 'arc'] 
        slots = ['kinetic', 'energy', 'power', 'ability']
        killType = ['rapid', 'precision', 'multi'] 
        abilities = ['melee', 'super', 'grenade']
        planets = ['edz', 'titan', 'moon', 'nessus', 'tangled shore', 'dreaming city', 'mercury', ' io', 'mars']
        activities = ['crucible', 'gambit', 'strike', 'nightfall', 'raid']

        self.Tier0 = slots

        self.Tier1 = weapons + abilities

        self.Tier2 = elements + killType + targets

        self.Tier3 = combatants

        self.Tier4 = planets

        self.Tier5 = activities

        #Mutually Exclusive buckets mean the objective in the same bucket can't happen at the same time
        exclusiveBuckets = [weapons, combatants, elements, slots, abilities, planets]

        self.exclusiveData = {}

        for bucket in exclusiveBuckets:
            self.exclusiveData.update(makeExclusive(bucket))

        self.exclusiveData['kinetic'] += elements

        #dprint(exclusiveData)


    def makeExclusive(self, items):
        data = {}
        for i in range(len(items)):
            data[items[i]] = items[:i] + items[i+1:]
        return data

        
    def performOptimisation(self, player):
        profile = self.getPlayerData(player)

        playerId = profile[1]
        playerType = profile[0]

        items = self.getAllItems(playerType, playerId)

        characters = self.getCharacters(playerType, playerId)

        bounties = self.getBounties(items, characters)
        weapons = self.getWeapons(items, characters)


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