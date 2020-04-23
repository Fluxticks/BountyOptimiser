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

import ahocorasick as aho
from time import process_time_ns

TRACE = 9

logger = makeLogger('Optimiser', logLevel=logging.INFO)

class Optimise():

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest
        logger.debug('Manifest loc: %s', self._manifestLoc)

    def buckets(self, weapons):

        enemies = {'cabal' : ['edz','io','mars','tangled shore'], 'fallen' : ['edz', 'titan', 'nessus', 'tangled shore', 'moon'], 'hive' : ['titan','mars','tangled shore', 'dreaming city', 'moon'], 'taken':['edz', 'io', 'dreaming city'], 'scorn':['tangled shore','dreaming city'], 'vex':['io','nessus', 'moon'], 'guardian':['crucible']}

        locations = ['edz','io','mars','tangled shore', 'titan', 'moon', 'dreaming city', 'crucible']

        A = aho.Automaton(value_type=aho.STORE_LENGTH)

        keys = locations + list(enemies.keys()) + weapons

        for idx, key in enumerate(keys):
            A.add_word(key,len(key))

        return A

        
    def performOptimisation(self, player):
        profile = self.getPlayerData(player)

        playerId = profile[1]
        playerType = profile[0]

        items = self.getAllItems(playerType, playerId)

        characters = self.getCharacters(playerType, playerId)

        bounties = self.getBounties(items, characters)
        items,weapons = self.getWeaponBuckets(items, characters)

        self.buckets(weapons)


    def dataToBounty(self, bounty):
        manifest = bounty.get('manifest')
        itemHash = bounty.get('itemHash')
        description = manifest.get('displayProperties').get('description')
        objectives = manifest.get('objectives').get('objectiveHashes')


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
                        bounties[character].append(self.dataToBounty(item))
                        logger.debug('Appended hashed bounty for character %s : %s', character, item.get('itemHash'))

        logger.trace('Bounty data: %s', bounties)
        logger.info('Done finding bounties for all characters (%d)', len(characterIds))
        return bounties


    def getWeaponBuckets(self, items, characterIds):
        weaponHashes = [BucketEnum.KINETIC_WEAPONS, BucketEnum.ENERGY_WEAPONS, BucketEnum.POWER_WEAPONS]
        characterInventories = items.get('characterInventories').get('data')
        vaultInventory = items.get('profileInventory').get('data').get('items')
        items = vaultInventory + self.makeListFromCharItems(characterInventories)

        logger.trace('Weapons data: %s', items)
        logger.info("Got all items for characters (%d) and Vault", len(characterIds))

        kinetic = {}
        energy = {}
        power = {}
        weapons = []

        for item in items:
            manifestItem = self.getValueFromTable(hashID(item.get('itemHash')), 'InventoryItem')
            bucketHash = manifestItem.get('inventory').get('bucketTypeHash')
            itemInstance = item.get('itemInstanceId')
            weaponType = str(manifestItem.get('itemTypeDisplayName')).lower()

            wasWeapon = False

            if not in weapons:
                weapons.append(weaponType)

            if bucketHash == BucketEnum.KINETIC_WEAPONS:
                if not kinetic.get(weaponType):
                    kinetic[weaponType] = []
                kinetic[weaponType].append(itemInstance)
                wasWeapon = True
            elif bucketHash == BucketEnum.ENERGY_WEAPONS:
                if not energy.get(weaponType):
                    energy[weaponType] = []
                energy[weaponType].append(itemInstance)
                wasWeapon = True
            elif bucketHash == BucketEnum.POWER_WEAPONS:
                if not power.get(weaponType):
                    power[weaponType] = []
                power[weaponType].append(itemInstance)
                wasWeapon = True
            
            if wasWeapon:
                logger.trace('Type: %s, hash: %s, instance: %s', weaponType, bucketHash, itemInstance)

        power['bow'] = power.pop('combat bow', None)
        energy['bow'] = energy.pop('combat bow', None)
        kinetic['bow'] = kinetic.pop('combat bow', None)
        try:
            weapons.remove('combat bow')
            weapons.append('bow')
            logger.debug('Replaced combat bow with bow')
        except:
            pass

        logger.trace('Got power bucket: %s', self.power)
        logger.trace('Got energy bucket: %s', self.energy)
        logger.trace('Got kinetic bucket: %s', self.kinetic)

        logger.info('Got weapon buckets!')
        
        return (items, weapons)

    def makeListFromCharItems(self, characters):
        charIds = list(characters.keys())

        items = []

        for charId in charIds:
            items += characters.get(charId).get('items')

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
            logger.trace('Searching manifest with statement: %s', statement)
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