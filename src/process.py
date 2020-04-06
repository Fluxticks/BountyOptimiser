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


    def getInventory(self, membershipType, membershipId):
        response = self._api.getProfileInventory(membershipType, membershipId)
        logger.debug('Got response for GetInventory call: %s', response)
        
        items = response.get('profileInventory').get('data').get('items')

        logger.debug('Items retrieved from api call: %s', items)

        tracked_enums = [BucketEnum.VAULT, BucketEnum.KINETIC_WEAPONS, BucketEnum.ENERGY_WEAPONS, BucketEnum.POWER_WEAPONS]

        for item in items:
            dehashed = unHashToId(item.get('bucketHash'))
            if unHashToId not in tracked_enums:
                items.remove(item)

        logger.debug('Filtered items for vault and weapons: %s', items)

        return items

    def getBounties(self, membershipType, membershipId, characterIds):
        response = self._api.getProgression(membershipType, membershipId)
        characterData = response.get('characterUninstancedItemComponents')
        objectives = {}
        for character in characterIds:
            objectives[character] = characterData.get(character).get('objectives')
        
        return objectives
        

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
        self._profile = self.getPlayerData(player)

        playerId = self._profile[1]
        playerType = self._profile[0]

        self._characters = self.getCharacters(playerType, playerId)

        print(self._objectives)

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
        