from api import API
from enums import ComponentTypeEnum, StatsEnum, ItemCategoryEnum, BucketEnum, CategoryEnum
from util import makeColorLog, makeLogger, dprint
from util import unHashToId as hashID
from util import DEBUG_TRACE_NUM as TRACE
import logging
import sqlite3
import json
import re
from itertools import chain
import urllib.error as urle
import sys

from Bucket import Bucket
from Bounty import Bounty

import ahocorasick as aho
from time import process_time_ns
import pickle

from Exceptions import APIException, GeneralException, ManifestError, DiscordError

logger = makeLogger('Optimiser', logLevel=logging.INFO)


class Optimise:

    def __init__(self, token, manifest):
        logger.debug('Initialised optimiser')
        self._api = API(token)
        self._manifestLoc = manifest
        logger.debug('Manifest loc: %s', self._manifestLoc)

    def buckets(self, weapons, others):

        # enemies = {'cabal' : ['edz','io','mars','tangled shore'], 'fallen' : ['edz', 'titan', 'nessus', 'tangled shore', 'moon'], 'hive' : ['titan','mars','tangled shore', 'dreaming city', 'moon'], 'taken':['edz', 'io', 'dreaming city'], 'scorn':['tangled shore','dreaming city'], 'vex':['io','nessus', 'moon'], 'guardian':['crucible']}

        # locations = ['edz','io','mars','tangled shore', 'titan', 'moon', 'dreaming city', 'crucible']

        with open('automaton', 'rb') as f:
            A = pickle.load(f)

        logger.debug('Loaded automaton with keys: %s', list(A.keys()))

        keys = list(weapons.keys()) + list(others.keys())

        logger.debug('keys: %s', keys)

        for index, word in enumerate(keys):
            A.add_word(word, (index, word))

        A.make_automaton()

        logger.debug('Automaton kind: %s , store: %s, size: %s', A.kind, A.store, A.__sizeof__())

        return A

    def performOptimisation(self, player=None, index=None, member=None, platform=None):

        if player is None and (member is None or platform is None):
            raise ValueError(
                "You must supply your Display Name or your MemeberID and your PlatformID. MemberID and PlatformID can be found using the !help command")

        t1 = process_time_ns()

        doneBuckets = None

        try:

            if player is not None:
                profile = self.getPlayerData(player, index)
                assert profile is not None, "Unable to get profile data"
                member = profile[1]
                platform = profile[0]

            items = self.getAllItems(platform, member)
            assert items is not None, "Unable to get item data"

            characters, displayName = self.getCharacters(platform, member)
            assert characters is not None, "Unable to get character ids"

            characterData = self.getCharacterData(platform, member, characters)
            assert characterData is not None, "Unable to get character data"

            bounties = self.getBounties(items, characters)
            assert bounties is not None, "Unable to get bounty data"
            weaponIdentifiers = self.getWeaponBuckets(items, characters)
            assert weaponIdentifiers is not None, "Unable to get weapon data"

            with open('identifiers', 'rb') as f:
                otherIdentifiers = pickle.load(f)

            automaton = self.buckets(weaponIdentifiers, otherIdentifiers)
            assert automaton is not None, "Unable to load automaton"

            wordedBounites = self.findWordsInAll(characters, bounties, automaton, weaponIdentifiers, otherIdentifiers)
            assert wordedBounites is not None, "There was an error when trying to find key words"

            doneBuckets = self.allBuckets(characters, wordedBounites)

        except AssertionError as e:
            logger.error("Assertion Error: %s", e.args)

        t2 = process_time_ns()

        logger.debug('Finished task in %s time!', float(t2 - t1) / 1000000000)
        logger.info('Finished finding optimal bounties!')

        return {'data': doneBuckets, 'name': displayName, 'id': member, 'type': platform, 'characters':characterData}

    def allBuckets(self, characters, bounties):
        logger.info('Calculating buckets!')
        out = {}

        for character in characters:
            out[character] = self.doBuckets(bounties.get(character))
            if out[character] is not None:
                logger.debug('For character %s, got final buckets (%s) of: %s', character, len(out[character]),
                             [str(x) for x in out[character]])

        return out

    def doBuckets(self, bounties):
        logger.info('Next character...')
        if bounties is None:
            return None

        buckets = []

        for bounty in bounties:
            result = False
            for bucket in buckets:
                result = bucket.add(bounty)
            if not result:
                buckets.append(Bucket(bounty))

        return self.trim(buckets)

    def trim(self, buckets):
        logger.info('Trimming buckets')

        # print([len(x) for x in buckets])

        buckets.sort(key=lambda x: len(x), reverse=True)

        # print([len(x) for x in buckets])
        # print([str(x) for x in buckets])
        for i in range(len(buckets)):
            current = buckets[i]
            current = current.bounties
            # logger.debug('Triming %s bucket from others...', current)
            for j in range(i + 1, len(buckets)):
                # logger.debug('Trimming bucket: %s', buckets[j])
                buckets[j].trim(current)

        # print([len(x) for x in buckets])

        logger.info('Done trimming!')

        return list(filter(lambda a: len(a) > 0, buckets))

    def findWordsInAll(self, characters, bounties, A, weaponIdentifiers, otherIdentifiers):
        logger.info('Finding keywords in bounties')
        data = dict.fromkeys(characters)

        for character in characters:
            logger.debug('Doing character: %s', character)
            data[character] = self.findWords(bounties.get(character), A, weaponIdentifiers, otherIdentifiers)

        logger.debug('Got keywords for all characters: %s', data)
        logger.info('Found keywords for all characters!')
        # dprint(data)
        return data

    def findWords(self, bounties, A, weaponIdentifiers, otherIdentifiers):
        for bounty in bounties:
            description = bounty.description.lower()
            logger.debug('For description: %s getting items', description)
            counter = 0
            for end_index, (insert_order, original_value) in A.iter(description):
                # Original value is the word found
                # start_index = end_index - len(original_value) + 1
                # print((start_index, end_index, (insert_order, original_value)))
                # Checks if somehow there was a fuckup
                # assert description[start_index:start_index + len(original_value)] == original_value
                counter += 1
                if original_value in weaponIdentifiers:
                    bounty.addWeapon(weaponIdentifiers.get(original_value), original_value)
                else:
                    bounty.addGeneral(otherIdentifiers.get(original_value), original_value)
            logger.debug('Bounty data: %s', bounty.data)
        return bounties

    def dataToBounty(self, bounty):
        manifest = bounty.get('manifest')
        itemHash = bounty.get('itemHash')
        description = manifest.get('displayProperties').get('description')
        title = manifest.get('displayProperties').get('name')
        return Bounty(itemHash, description, title)

    def makeListFromCharItems(self, characters):
        charIds = list(characters.keys())

        items = []

        for charId in charIds:
            items += characters.get(charId).get('items')

        return items

    def getAllItems(self, membershipType, membershipId):
        logger.debug('Getting All Items')
        try:
            response = self._api.getProfileInventory(membershipType, membershipId)
            logger.trace('Got response for GetInventory call: %s', response)
            logger.debug('Got all items for member %s (%s)', membershipId, membershipType)
            return response
        except APIException as e:
            logger.error('There was an error when trying to retrieve items: %s, url: %s', e.message, e.url)
            raise DiscordError(e.message)

    def getBounties(self, items, characterIds):
        logger.debug('Getting Bounties')
        characterInventories = items.get('characterInventories').get('data')

        bounties = {}

        try:
            for character in characterIds:
                bounties[character] = []
                for item in characterInventories.get(character).get('items'):
                    if item.get('bucketHash') == BucketEnum.QUESTS and item.get('expirationDate') is not None:
                        itemDefinition = self.getValueFromTable(hashID(item.get('itemHash')),
                                                                'DestinyInventoryItemDefinition')
                        if CategoryEnum.QUEST_STEP not in itemDefinition.get('itemCategoryHashes'):
                            item['manifest'] = itemDefinition
                            bounty = self.dataToBounty(item)
                            bounties[character].append(bounty)
                            logger.debug('Appended hashed bounty for character %s : %s', character,
                                         item.get('itemHash'))
                            logger.trace('Bounty: description: %s', bounty.description)

            logger.trace('Bounty data: %s', bounties)
            logger.info('Done finding bounties for all characters (%d)', len(characterIds))
        except AttributeError as e:
            logger.error('There was an error getting bounties from item data')
            return None
        except ManifestError as e:
            logger.error('There was an error when accesing the DB (%s) using the statement: %s', self._manifestLoc,
                         e.SQL)
            return None

        return bounties

    def getWeaponBuckets(self, items, characterIds):
        logger.debug('Getting weapons and buckets')
        weaponHashes = {BucketEnum.KINETIC_WEAPONS: "kinetic", BucketEnum.ENERGY_WEAPONS: "energy",
                        BucketEnum.POWER_WEAPONS: "power"}
        characterInventories = items.get('characterInventories').get('data')
        vaultInventory = items.get('profileInventory').get('data').get('items')
        items = vaultInventory + self.makeListFromCharItems(characterInventories)

        logger.trace('Weapons data: %s', items)
        logger.info("Got all items for characters (%d) and Vault", len(characterIds))

        weapons = {}
        current = None
        try:
            for item in items:
                current = item
                manifestItem = self.getValueFromTable(hashID(item.get('itemHash')), 'InventoryItem')
                bucketHash = manifestItem.get('inventory').get('bucketTypeHash')
                itemInstance = item.get('itemInstanceId')
                weaponType = str(manifestItem.get('itemTypeDisplayName')).lower()

                wasWeapon = False

                if bucketHash in weaponHashes:
                    if weaponType not in weapons:
                        weapons[weaponType] = set()
                    weapons[weaponType].add(weaponHashes.get(bucketHash))
                    wasWeapon = True

                if wasWeapon:
                    if weaponType not in weapons:
                        weapons.append(weaponType)
                    logger.trace('Type: %s, hash: %s, instance: %s', weaponType, bucketHash, itemInstance)

            weapons["bow"] = weapons.pop("combat bow", None)
            weapons[" machine gun"] = weapons.pop("machine gun", None)

            logger.trace("Got weapons: %s", weapons)

            logger.info('Got weapon buckets!')
        except AttributeError as e:
            logger.error('There was an error when accesing the data in item %s, (%s)', current, e)
        except ManifestError as e:
            logger.error('There was an error when accesing the DB (%s) using the statement: %s', e.SQL)
        return weapons

    def getCharacters(self, membershipType, membershipId):
        logger.debug('Getting character ids')
        try:
            response = self._api.getProfile(membershipType, membershipId)
            characters = response.get('profile').get('data').get('characterIds')
            displayName = response.get('profile').get('data').get('userInfo').get('displayName')
            logger.debug('Got %s character ids', characters)
            logger.info('Got characters for %s (%s)', membershipId, membershipType)
        except APIException as e:
            logger.error('There was an error when getting Character Ids: %s', e.message)
        except AttributeError as e:
            logger.error('There was an error when accesing the data recieved: %s', response)
        return characters, displayName

    def getCharacterData(self, membershipType, membershipId, characterIds):
        logger.debug('Getting character data')
        characterData = {}
        try:
            for character in characterIds:
                characterData[character] = {}
                response = self._api.getCharacter(membershipType,membershipId,character).get('character').get('data')
                characterData[character]['emblem'] = response.get('emblemBackgroundPath')
                characterData[character]['light'] = str(response.get('light'))
                characterData[character]['class'], characterData[character]['gender'], characterData[character]['race'] = self.getCharacterIdentity(response.get('classHash'),response.get('genderHash'),response.get('raceHash'))
            logger.debug('Got character data; %s', characterData)
            return characterData
        except APIException as e:
            logger.error('There was an error when getting character data: %s', e.message)
        except AttributeError as e:
            logger.error('There was an error when accesing the data recieved: %s', response)

    def getCharacterIdentity(self, classHash, genderHash, raceHash):
        classData = self.getValueFromTable(hashID(classHash), 'Class')
        className = classData.get('displayProperties').get('name')
        genderData = self.getValueFromTable(hashID(genderHash), 'Gender')
        genderName = genderData.get('displayProperties').get('name')
        raceData = self.getValueFromTable(hashID(raceHash), 'Race')
        raceName = raceData.get('displayProperties').get('name')
        return (className,genderName,raceName)
            

    def getPlayerData(self, player, index):
        logger.debug('Getting player data')
        try:
            response = self._api.getPlayer(player, index=index)
            pId = response.get('membershipId')
            pType = response.get('membershipType')
            displayName = response.get('displayName')

            logger.trace('Display Name: %s, MemberId: %s, MemberType:%s', displayName, pType, pId)

            logger.info('Got player data for %s', player)

            return [pType, pId, displayName]
        except urle.HTTPError as e:
            logger.error('HTTP error in Get Player Data request')
        except urle.URLError as e:
            logger.error('URL error encountered! Error: %s', str(e.reason))
        except APIException as e:
            logger.error('There was an exception when getting data from the Destiny 2 API on URL: %s', e.url)
            raise DiscordError(e.message)
        except DiscordError as e:
            # TODO fix this.
            raise DiscordError(e.message)
        except BaseException as e:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logger.error("Encounterd unknown error! Message: %s ", ex_value)
        return None

    def getValueFromTable(self, valueId, tableName):
        if 'Destiny' not in tableName:
            tableName = 'Destiny' + tableName
        if 'Definition' not in tableName:
            tableName += 'Definition'
        statement = f'SELECT json FROM {tableName} WHERE id = {valueId}'
        try:
            conn = sqlite3.connect(self._manifestLoc)
            cursor = conn.cursor()
            logger.trace('Searching manifest with statement: %s', statement)
            cursor.execute(statement)
            data = cursor.fetchone()
            conn.close()
            # Removes the tuple anmd gives the data as str
            data = data[0]
            # Turn data str into dict for easier access
            data = json.loads(data)
            return data
        except:
            raise ManifestError(f"There was an error when accessing the database", SQL=statement)
