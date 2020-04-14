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

logger = makeLogger('opt', logLevel=logging.DEBUG)

class Optimise():

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest
        logger.debug('Manifest loc: %s', self._manifestLoc)
        self.makeBuckets()

    def makeBuckets(self):
        
        #General keywords
        weapons = ['auto rifle', 'scout rifle', 'hand cannon', 'sniper', 'sidearm', 'pulse rifle', 'submachine gun', 'shotgun', 'fusion rifle', 'trace rifle', 'grenade launcher', 'rocket launcher', 'linear fusion rifle', 'sword', 'heavy machine gun']
        combatants = ['fallen', 'vex', 'hive', 'taken', 'scorn', 'cabal', 'guardians'] 
        targets = ['opponents', 'combatants', 'enemies', 'any target'] 
        elements = ['solar', 'void', 'arc'] 
        slots = ['kinetic', 'energy', 'power', 'ability']
        killType = ['rapid', 'precision', 'multi'] 
        abilities = ['melee', 'super', 'grenade']
        planets = ['edz', 'titan', 'moon', 'nessus', 'tangled shore', 'dreaming city', 'mercury', ' io', 'mars']
        activities = ['crucible', 'gambit', 'strike', 'nightfall', 'raid']

        #Activity keywords
        games = ['win', 'matches']

        #Crucible keywords
        crucible = ['clash', 'control', 'rumble', 'skirmish', 'supremacy', 'breakthrough', 'countdown', 'survival', 'iron banner']
        tasks = ['crests', 'control', 'charges']

        #Gambit keywords
        gambit = ['motes']

        #Location keywords
        location = ['chest', 'patrol', 'public event']

        Tier0 = slots
        Tier1 = weapons + abilities
        Tier2 = elements + killType + targets
        Tier3 = combatants
        Tier4 = planets + location
        Tier5 = activities

        self.Tiers = {0:Tier0,1:Tier1,2:Tier2,3:Tier3,4:Tier4,5:Tier5}

        logger.trace('Tiers created: %s', self.Tiers)

        #for key,value in self.Tiers.items():
        #    self.Tiers[key] = value.sort(key=lambda x: len(x.split(' ')), reverse=False)

        #Mutually Exclusive buckets mean the objective in the same bucket can't happen at the same time
        exclusiveBuckets = [weapons, combatants, elements, slots, abilities, planets]
        self.exclusiveData = {}
        for bucket in exclusiveBuckets:
            self.exclusiveData.update(self.makeExclusive(bucket))

        self.exclusiveData['kinetic'] += elements

        logger.trace('Exclusive data: %s', self.exclusiveData)

        #dprint(exclusiveData)

        #self.keywords = weapons + combatants + targets + elements + slots + killType + abilities + planets + activities  + games + crucible + tasks + gambit + location

        #self.keywords.sort(key=lambda x: len(x.split(' ')), reverse=False)


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

        bounties = self.makeBountyFromAPIData(bounties, characters)

        logger.debug('Bounties: %s', bounties)

        

    def makeBountyFromAPIData(self, data, characters):

        bounties = {}

        for character in characters:
            bounties[character] = []
            characterData = data.get(character)
            for bounty in characterData:
                tiersFound = self.getTiers(bounty)
                bounties[character].append(Bounty(bounty.get('itemHash'), tiersFound))

        return bounties

    def getTiers(self, bounty):
        tiersFound = {}

        description = bounty.get('manifest').get('displayProperties').get('description')
        description = description.lower()

        for tier, words in self.Tiers.items():
            for word in words:
                if word in description:
                    if not tiersFound.get(tier):
                        tiersFound[tier] = []
                    tiersFound[tier].append(word)

        return tiersFound



    def getAllItems(self, membershipType, membershipId):
        response = self._api.getProfileInventory(membershipType, membershipId)
        logger.debug('Got response for GetInventory call')

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
                manifestItem = self.getValueFromTable(unHashToId(item.get('itemHash')), 'DestinyInventoryItemDefinition')
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
        logger.debug('Character Ids: %s', characters)
        
        return characters


    def getPlayerData(self, player):
        response = self._api.getPlayer(player)

        pId = response.get('membershipId')
        pType = response.get('membershipType')
        displayName = response.get('displayName')

        logger.debug('Player ID: %s, Player Type: %s, Display Name: %s', pId, pType, displayName)

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