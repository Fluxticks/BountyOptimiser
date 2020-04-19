from urllib.request import Request, urlopen
import json
import os
import os.path
import logging
import urllib.error
import zipfile
from util import makeLogger, makeColorLog

#----------------------------------------------------------------------------------------------------------------------

BUNGIE = "https://www.bungie.net"
BASE = BUNGIE + "/Platform/Destiny2/"
logger = makeLogger('API')

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

#TODO: Add getItem

class API():

    def __init__(self, key):
        self._key = key

    def makeRequest(self, url):
        req = Request(url)
        req.add_header('X-API-KEY', self._key)
        return req

    def GET(self, url:str):
        try:
            req = self.makeRequest(url)
            content = urlopen(req).read()
            logger.debug('Made get request: %s and got content of type: %s', url, type(content))
            return contentToDict(content)
        except urllib.error.HTTPError as e:
            logger.error('Encountered an exception while trying to perform GET request: %s', e.reason)
            return None
        except Exception as ex:
            logger.error('An unexpected error occured: %s', ex)


    def getPlayer(self, name:str):
        url = BASE + f"SearchDestinyPlayer/-1/{name}/"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Player: Name (%s)', name)
        else:
            logger.info('Got player data for %s', name)
            logger.debug('Player Content: %s', content)
            return content


    def getProfile(self, membershipType, membershipId, components='100'):
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/?components={component}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Player Profile: MembershipId (%s), MembershipType (%s)', membershipId, membershipType)
        else:
            logger.info('Got profile data for player id %s on platform id %s', membershipId, membershipType)
            logger.debug('Profile Content: %s', content)
        
        return content


    def getCharacter(self, membershipType, membershipId, characterId, components='200'):
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components={component}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Profile Character: CharacterId (%s), MembershipId (%s), MembershipType (%s)', characterId, membershipId, membershipType)
        else:
            logger.info('Got character data for characterid %s for profileid %s', characterId, membershipId)
            logger.debug('Character Content: %s', content)

        return content


    #Get an individual characters inventory
    def getCharacterInventory(self, membershipType, membershipId, characterId, components='205'):
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components={components}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Character Inventory: CharacterId (%s), MembershipId (%s), MembershipType (%s)', characterId, membershipId, membershipType)
        else:
            logger.info('Got character data for characterid %s for profileid %s', characterId, membershipId)
            logger.debug('Character Inventory Content: %s', content)

        return content


    #Gets all items including quests and bounties
    def getProfileInventory(self, membershipType, membershipId, components='102,201'):
        url = BASE + f"{membershipType}/Profile/{membershipId}/?components={components}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Profile Inventory: MembershipId (%s), MembershipType (%s)', membershipId, membershipType)
        else:
            logger.info('Got profile inventory data for profile id: %s (Type:%s)', membershipId, membershipType)
            logger.debug('Profile Inventory Content: %s', content)

        return content

    def getItem(self, membershipType, membershipId, itemInstance, components='300,302,304,305'):
        url = BASE + f"{membershipType}/Profile/{membershipId}/Item/{itemInstance}/?components={components}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for item %s in profile %s (%s)', itemInstance, membershipId, membershipType)
        else:
            logger.debug('Item data for item %s and profile %s: %s', itemInstance, membershipId, content)
            loggger.info('Got item data for item: %s', itemInstance)

        return content


    #Update Manifest
    def manifestUpdate(self, localization):
        url = BASE + "Manifest"
        content = self.GET(url)
        if content is None:
            logger.error('Got None in GET request for Manifest data: localization (%s)', localization)
        else:
            logger.info('Got manifest data')
            worldContentsPaths = content.get('mobileWorldContentPaths')
            lang = worldContentsPaths.get(localization)
            filename = os.path.basename(lang)
            filename = filename.split('.')[0]
            if not os.path.isfile(filename+".sqlite3"):
                url = BUNGIE + f"/common/destiny2_content/sqlite/{localization}/{filename}.content"
                req = self.makeRequest(url)
                logger.debug('Making request %s', req)
                with urlopen(req) as dl_file:
                    with open('manifest.zip', 'wb') as out_file:
                        out_file.write(dl_file.read())
                with zipfile.ZipFile('manifest.zip', 'r') as zip_ref:
                    zip_ref.extractall('.')

                logger.info('Downloaded new manifest: %s', filename)

                os.remove('manifest.zip')
                os.rename(filename+".content", filename+".sqlite3")
            else:
                logger.info('Not downloading new manifest, staying on %s', filename)

        return filename + '.sqlite3'
