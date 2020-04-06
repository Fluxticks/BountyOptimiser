from api import API
from enums import MembershipTypeEnum, ComponentTypeEnum, StatsEnum, ItemCategoryEnum, BucketEnum
from util import makeColorLog, makeLogger, unHashToId
import logging
import sqlite3
import json

logger = makeColorLog('Optimiser', logLevel=logging.INFO)

class Optimise():

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest


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
                if item.get('bucketHash') == BucketEnum.QUESTS:
                    item['manifest'] = self.getValueFromTable(unHashToId(item.get('itemHash')), 'DestinyInventoryItemDefinition')
                    bounties[character].append(item)
                    logger.debug('Appended hashed item for character %s : %s', character, item.get('itemHash'))

        logger.info('Done finding bounties for all characters (%d)', len(characterIds))
        logger.debug('Bounty data: %s', bounties)
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

        logger.info("Done finding weapons for all characters (%d) and Vault", len(characterIds))
        logger.debug('Weapons data: %s', items)
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

    def OptimiseBounties(self, player):
        profile = self.getPlayerData(player)

        playerId = profile[1]
        playerType = profile[0]

        items = self.getAllItems(playerType, playerId)

        characters = self.getCharacters(playerType, playerId)

        bounties = self.getBounties(items, characters)
        weapons = self.getWeapons(items, characters)

        print(weapons)


    def getValueFromTable(self, valueId, tableName):
        try:
            conn = sqlite3.connect(self._manifestLoc)
            cursor = conn.cursor()
            cursor.execute(f'SELECT json FROM {tableName} WHERE id = {valueId}')
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
        