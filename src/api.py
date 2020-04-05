from urllib.request import Request, urlopen
import json
import os
import os.path
import logging
from coloured_log import ColoredFormatter
import urllib.error
import zipfile
import colorlog


LOG_LEVEL = logging.INFO
LOGFORMAT = '  %(name)s : %(log_color)s%(levelname)-8s%(reset)s | %(message)s (%(filename)s:%(lineno)d)'

stream = colorlog.StreamHandler()
stream.setFormatter(colorlog.ColoredFormatter(LOGFORMAT))

#LOGFORMAT = '[%(name)s][%(levelname)s]  %(message)s (%(filename)s:%(lineno)d)'
#LOGFORMAT = '  [%(name)s][%(levelname)-8s] | %(message)s (%(filename)s:%(lineno)d)'
#formatter = ColoredFormatter(LOGFORMAT)

#stream = logging.StreamHandler()
#stream.setLevel(LOG_LEVEL)
#stream.setFormatter(formatter)

file = logging.FileHandler('api.log')
file.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file.setFormatter(file_format)

logger = logging.getLogger('API')
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)
logger.addHandler(file)

#----------------------------------------------------------------------------------------------------------------------

BUNGIE = "https://www.bungie.net"
BASE = BUNGIE + "/Platform/Destiny2/"

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
            logger.debug('Made get request: %s and got content of type: %s', req, type(content))
            return contentToDict(content)
        except urllib.error.HTTPError as e:
            logger.error('Encountered an exception while trying to perform GET request: %s', e.reason)
            return None
        except Exception as ex:
            logger.error('An unexpected error occured: %s', ex)

    #Get Profile
    def getPlayer(self, name:str):
        url = BASE + f"SearchDestinyPlayer/-1/{name}/"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Player: Name (%s)', name)
        else:
            logger.info('Got player data for %s', name)
            logger.debug('Player Content: %s', content)
            return content


    def getProfile(self, membershipType, membershipId, components=100):
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/?components={component}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Player Profile: MembershipId (%s), MembershipType (%s)', membershipId, membershipType)
        else:
            logger.info('Got profile data for player id %s on platform id %s', membershipId, membershipType)
            logger.debug('Profile Content: %s', content)
        
        return content


    #Get Character
    def getCharacter(self, membershipType, membershipId, characterId, components=200):
        component = splitComponents(components)
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components={component}"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Profile Character: CharacterId (%s), MembershipId (%s), MembershipType (%s)', characterid, membershipId, memebershipType)
        else:
            logger.info('Got character data for characterid %s for profileid %s', characterid, membershipId)
            logger.debug('Character Content: %s', content)

        return content


    #Get Character Inventory
    def getCharacterInventory(self, membershipType, membershipId, characterId):
        url = BASE + f"{membershipType}/Profile/{membershipId}/Character/{characterId}/?components=205"
        content = self.GET(url)
        if content is None:
            logger.error('Got None from GET request for Character Inventory: CharacterId (%s), MembershipId (%s), MembershipType (%s)!', characterid, membershipId, memebershipType)
        else:
            logger.info('Got character data for characterid %s for profileid %s', characterid, membershipId)
            logger.debug('Character Inventory Content: %s', content)

        return content


    #Get Bounties
    def getProgression(self, memebershipType, membershipId):
        url = BASE + f"{memebershipType}/Profile/{membershipId}/?components=301"
        content = self.GET(url)
        if content is None:
            logger.error('Got None in GET request for Profile Progression: MembershipId (%s), MembershipType (%s)', membershipId, memebershipType)
        else:
            logger.info('Got Progression data for membershipid %s ', membershipId)
            logger.debug('Profile Progression: %s', content)

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
                req = makeRequest(url)
                logger.debug('Making request %s', req)
                with urlopen(req) as dl_file:
                    with open('manifest.zip', 'wb') as out_file:
                        out_file.write(dl_file.read())
                with zipfile.ZipFile('manifest.zip', 'r') as zip_ref:
                    zip_ref.extractall('.')

                os.remove('manifest.zip')
                os.rename(filename+".content", filename+".sqlite3")
            else:
                logger.info('Not downloading manifest as no update')
