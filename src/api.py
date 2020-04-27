from urllib.request import Request, urlopen
import urllib.parse
import json
import os
import os.path
import logging
import urllib.error
import zipfile
from util import makeLogger, makeColorLog
import glob
from Exceptions import APIException
import sys

from util import DEBUG_TRACE_NUM as TRACE

#----------------------------------------------------------------------------------------------------------------------

BUNGIE = "https://www.bungie.net"
BASE = BUNGIE + "/Platform/Destiny2/"
logger = makeLogger('API', logLevel=logging.DEBUG)

#----------------------------------------------------------------------------------------------------------------------

def splitComponents(components):
    out = ""
    if isinstance(components, list):
        for component in components:
            out += component + ","
        out = out[:-1]
    else:
        out = str(components)

    return out   
    

def contentToDict(content:bytes):
    decoded = content.decode()
    dictionary = json.loads(decoded)
    logger.debug('Decoded data from content and got data of type: %s', type(dictionary))
    data = dictionary.get('Response')
    logger.debug('Response Type: %s', type(data))
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        return data[0]
    else:
        return None

#----------------------------------------------------------------------------------------------------------------------

class API():

    def __init__(self, key):
        logger.debug('Key: %s', key)
        self._key = key

    def __makeRequest(self, url):
        req = Request(url)
        req.add_header('X-API-KEY', self._key)
        return req

    def GET(self, url:str):
        try:
            req = self.__makeRequest(url)
            content = urlopen(req).read()
            logger.debug('Made get request: %s and got content of type: %s', url, type(content))
            return contentToDict(content)
        except urllib.error.HTTPError as e:
            logger.error('Encountered an exception while trying to perform GET request: %s', e.reason)
        except BaseException as ex:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logger.error('An unexpected error occured: %s', ex_value)


    def getPlayer(self, name:str):
        logger.debug('Getting player: %s', name)
        url = BASE + f"SearchDestinyPlayer/-1/{name.replace(' ','%20')}/"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Destiny Player Lookup", url=url)
        else:
            logger.trace('Player Content: %s', content)
            return content


    def getProfile(self, membershipType, membershipId, components='100'):
        logger.debug('Getting Profile')
        logger.trace('MembershipType: %s, MembershipId: %s, Components: %s', membershipType, membershipId, components)
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/?components={component}"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Player Profile Lookup", url=url)
            #logger.error('Got None from GET request for Player Profile: MembershipId (%s), MembershipType (%s)', membershipId, membershipType)
        else:
            logger.trace('Profile Content: %s', content)
        
        return content


    def getCharacter(self, membershipType, membershipId, characterId, components='200'):
        logger.debug('Getting character')
        logger.trace('MembershipType: %s, MembershipId: %s, CharacterId: %s, Components: %s', membershipType, membershipId, characterId, components)
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components={component}"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Profile Character Lookup",url=url)
            #logger.error('Got None from GET request for Profile Character: CharacterId (%s), MembershipId (%s), MembershipType (%s)', characterId, membershipId, membershipType)
        else:
            logger.trace('Character Content: %s', content)
        return content


    #Get an individual characters inventory
    def getCharacterInventory(self, membershipType, membershipId, characterId, components='205'):
        logger.debug('Getting character inventory')
        logger.trace('MembershipType: %s, MembershipId: %s, CharacterId: %s, Components: %s', membershipType, membershipId, characterId, components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components={components}"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Character Inventory Lookup",url=url)
            #logger.error('Got None from GET request for Character Inventory: CharacterId (%s), MembershipId (%s), MembershipType (%s)', characterId, membershipId, membershipType)
        else:
            logger.trace('Character Inventory Content: %s', content)

        return content


    #Gets all items including quests and bounties
    def getProfileInventory(self, membershipType, membershipId, components='102,201'):
        logger.debug('Getting profile inventory')
        logger.trace('MembershipType: %s, MembershipId: %s, Components: %s', membershipType, membershipId, components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/?components={components}"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Profile Inventory Lookup", url=url)
            #logger.error('Got None from GET request for Profile Inventory: MembershipId (%s), MembershipType (%s)', membershipId, membershipType)
        else:
            logger.trace('Profile Inventory Content: %s', content)

        return content

    def getItem(self, membershipType, membershipId, itemInstance, components='300,302,304,305'):
        logger.debug('Getting item')
        logger.trace('MembershipType: %s, MembershipId: %s, ItemInstance: %s, Components: %s', membershipType, membershipId, itemInstance, components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/Item/{itemInstance}/?components={components}"
        content = self.GET(url)
        if content is None:
            raise APIException(message="Inventory Item Lookup",url=url)
            #logger.error('Got None from GET request for item %s in profile %s (%s)', itemInstance, membershipId, membershipType)
        else:
            logger.trace('Item data for item %s and profile %s: %s', itemInstance, membershipId, content)

        return content


    #Update Manifest
    def manifestUpdate(self, localization):
        logger.debug('Getting manifest update')
        logger.trace('Localization: %s', localization)
        url = BASE + "Manifest"
        content = self.GET(url)
        oldFile = self.__findOldFile(localization)
        if content is None:
            if oldFile is None:
                logger.critical('Was unable to get new manifest and no backup manifest exists!')
                return None
            else:
                logger.error('Got None in GET request for Manifest data: localization (%s), using old manifest', localization)
                return oldFile
        else:
            logger.info('Got manifest data')
            worldContentsPaths = content.get('mobileWorldContentPaths')
            lang = worldContentsPaths.get(localization)
            filename = os.path.basename(lang)
            filename = filename.split('.')[0]
            if (localization+"_"+filename+".sqlite3") != oldFile:
                url = BUNGIE + f"/common/destiny2_content/sqlite/{localization}/{filename}.content"
                req = self.__makeRequest(url)
                logger.debug('Making request %s', req)
                with urlopen(req) as dl_file:
                    with open('manifest.zip', 'wb') as out_file:
                        out_file.write(dl_file.read())
                with zipfile.ZipFile('manifest.zip', 'r') as zip_ref:
                    zip_ref.extractall('.')

                logger.info('Downloaded new manifest: %s', filename)

                os.remove('manifest.zip')
                os.rename(filename+".content", localization+"_"+filename+".sqlite3")
                if oldFile is not None:
                    os.remove(oldFile)
            else:
                logger.info('Not downloading new manifest, staying on %s', filename)

        return localization+"_"+filename + '.sqlite3'

    def __findOldFile(self, lang):
        for file in glob.glob("*.sqlite3"):
            if lang in file.split('_')[0]:
                return str(file)
        return None

