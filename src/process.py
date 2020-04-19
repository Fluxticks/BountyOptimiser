from api import API
from enums import ComponentTypeEnum, StatsEnum, ItemCategoryEnum, BucketEnum, CategoryEnum
from util import makeColorLog, makeLogger, dprint
from util import unHashToId as hashID
import logging
import sqlite3
import json
import re
from itertools import chain

from Bucket import Bucket
from Bounty import Bounty

# TODO: Streamline bucket creation and getting of weapons into single function!

TRACE = 9

logger = makeLogger('Optimiser', logLevel=logging.DEBUG)

class Optimise():

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest
        logger.debug('Manifest loc: %s', self._manifestLoc)

    def buckets(self, items):

        self.enemies = {'cabal' : ['edz','io','mars','tangled shore'], 'fallen' : ['edz', 'titan', 'nessus', 'tangled shore', 'moon'], 'hive' : ['titan','mars','tangled shore', 'dreaming city', 'moon'], 'taken':['edz', 'io', 'dreaming city'], 'scorn':['tangled shore','dreaming city'], 'vex':['io','nessus', 'moon'], 'guardian':['crucible']}

        self.locations = ['edz','io','mars','tangled shore', 'titan', 'moon', 'dreaming city', 'crucible']

        self.weapons = []

        self.kinetic = {}
        self.energy = {}
        self.power = {}

        for item in items:
            itemInstance = item.get('itemInstanceId')
            itemData = self.getValueFromTable(hashID(item.get('itemHash')), 'InventoryItem')
            weaponType = str(itemData.get('itemTypeDisplayName')).lower()
            bucketHash = itemData.get('inventory').get('bucketTypeHash')

            logger.trace('INFO: instance %s, type %s, hash %s', itemInstance, weaponType, bucketHash)

            if weaponType not in self.weapons:
                self.weapons.append(weaponType)

            if bucketHash == BucketEnum.KINETIC_WEAPONS:
                if not self.kinetic.get(weaponType):
                    self.kinetic[weaponType] = []
                self.kinetic[weaponType].append(itemInstance)
            elif bucketHash == BucketEnum.ENERGY_WEAPONS:
                if not self.energy.get(weaponType):
                    self.energy[weaponType] = []
                self.energy[weaponType].append(itemInstance)
            elif bucketHash == BucketEnum.POWER_WEAPONS:
                if not self.power.get(weaponType):
                    self.power[weaponType] = []
                self.power[weaponType].append(itemInstance)

        # In the api bows are called combat bows, but in game they are referenced as bows
        self.power['bow'] = self.power.pop('combat bow', None)
        self.energy['bow'] = self.energy.pop('combat bow', None)
        self.kinetic['bow'] = self.kinetic.pop('combat bow', None)
        if self.weapons.pop('combat bow', None) is not None:
            self.weapons.append('bow')

        logger.debug('Got all kinetic weapons: %s', self.kinetic)
        logger.debug('Got all energy weapons: %s', self.energy)
        logger.debug('Got all power weapons: %s', self.power)
        logger.info('Got all weapon types and slots')

        
    def performOptimisation(self, player):
        profile = self.getPlayerData(player)

        playerId = profile[1]
        playerType = profile[0]

        items = self.getAllItems(playerType, playerId)

        characters = self.getCharacters(playerType, playerId)

        bounties = self.getBounties(items, characters)
        weapons = self.getWeapons(items, characters)

        self.buckets(weapons)


    def makeBuckets(self, bounties, characters):
        logger.debug('Making buckets')
        buckets = {}

        for character in characters:
            buckets[character] = []
            for bounty in bounties:
                buckets[character].append(self.dataToBounty(bounty))

    def dataToBounty(self, bounty) -> Bounty:
        
        itemHash = bounty.get('itemHash')
        description = bounty.get('displayProperties').get('description')
        objectives = bounty.get('objectives').get('objectiveHashes')

    def searchDescription(self, description):
        description = description.lower()

        optionals = description.split(' or ')

        data = []

        for opt in optionals:
            data.append(self.findParts(opt))

        return data

    def findParts(self, description):
        pass
        # find weapon

        # find elements

        # find enemy type

        # find plant

        # find activity


    def getAllItems(self, membershipType, membershipId):
        response = self._api.getProfileInventory(membershipType, membershipId)
        logger.trace('Got response for GetInventory call: %s', response)
        logger.debug('Got all items for member %s (%s)', membershipId, membershipType)

        return response


    def getBounties(self, items, characterIds):
        characterInventories = items.get('characterInventories').get('data')

        bounties = {}

        for character in characterIds:
            bounties[character] = []
            for item in characterInventories.get(character).get('items'):
                if item.get('bucketHash') == BucketEnum.QUESTS and item.get('expirationDate') is not None:
                    itemDefinition = self.getValueFromTable(hashID(item.get('itemHash')), 'DestinyInventoryItemDefinition')
                    if CategoryEnum.QUEST_STEP not in itemDefinition.get('itemCategoryHashes'):
                        item['manifest'] = itemDefinition
                        bounties[character].append(item)
                        logger.debug('Appended hashed item for character %s : %s', character, item.get('itemHash'))

        logger.trace('Bounty data: %s', bounties)
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
                manifestItem = self.getValueFromTable(hashID(item.get('itemHash')), 'DestinyInventoryItemDefinition')
                if manifestItem.get('inventory').get('bucketTypeHash') in weaponHashes:
                    item['bucketHash'] = manifestItem.get('inventory').get('bucketTypeHash')
                    items.append(item)
                    logger.debug('Appended hased item from vault: %s', item.get('itemHash'))

        logger.trace('Weapons data: %s', items)
        logger.info("Done finding weapons for all characters (%d) and Vault", len(characterIds))
        return items

        
    def getCharacters(self, membershipType, membershipId):
        response = self._api.getProfile(membershipType, membershipId)
        characters = response.get('profile').get('data').get('characterIds')
        logger.debug('Got characters for %s (%s)', membershipId, membershipType)

        return characters


    def getPlayerData(self, player):
        response = self._api.getPlayer(player)

        pId = response.get('membershipId')
        pType = response.get('membershipType')
        displayName = response.get('displayName')

        logger.info('Got player data for %s', player)

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
            logger.debug('Loaded data into dict')
            return data
        except OSError as oserror:
            logger.error('An OS error occured: %s', oserror)
        except sqlite3.DatabaseError as dberror:
            logger.error('A DataBase Error occured while trying to access the manifest file: %s', dberror)
        except sqlite3.Error as generic:
            logger.error('A Generic Error occured while trying to access the manifest file: %s', generic)