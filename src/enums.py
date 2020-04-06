class MembershipTypeEnum:
    NONE = 0
    XBOX = 1
    PSN = 2
    STEAM = 3
    BLIZZARD = 4
    STADIA = 5
    DEMON = 10
    BUNGIENEXT = 254
    All = -1


class ComponentTypeEnum:
    NONE = '0'
    PROFILES = '100'
    VENDORRECEIPTS = '101'
    PROFILEINVENTORIES = '102'
    PROFILECURRENCIES = '103'
    PROFILEPROGRESSION = '104'
    PLATFORMSILVER = '105'
    CHARACTERS = '200'
    CHARACTERINVENTORIES = '201'
    CHARACTERPROGRESSIONS = '202'
    CHARACTERRENDERDATA = '203'
    CHARACTERACTIVITIES = '204'
    CHARACTEREQUIPMENT = '205'
    ITEMINSTANCES = '300'
    ITEMOBJECTIVES = '301'
    ITEMPERKS = '302'
    ITEMRENDERDATA = '303'
    ITEMSTATS = '304'
    ITEMSOCKETS = '305'
    ITEMTALENTGRIDS = '306'
    ITEMCOMMONDATA = '307'
    ITEMPLUGSTATES = '308'
    ITEMPLUGOBJECTIVES = '309'
    ITEMREUSABLEPLUGS = '310'
    VENDORS = '400'
    VENDORCATEGORIES = '401'
    VENDORSALES = '402'
    KIOSKS = '500'
    CURRENCYLOOKUPS = '600'
    PRESENTATIONNODES = '700'
    COLLECTIBLES = '800'
    RECORDS = '900'
    TRANSITORY = '1000'

class ItemCategoryEnum:
    WARLOCK_GEAR = 21
    TITAN_GEAR = 22
    HUNTER_GEAR = 23

#######################################################################
# All Enums must be unhashed in order for the manifest to be searched #
#######################################################################

class StatsEnum:
    HANDICAP = '2341766298'
    VOID_COST = '2399985800'
    VELOCITY = '2523465841'
    RECOIL_DIRECTION = '2715839340'
    SCORE_MULTIPLIER = '2733264856'
    EFFICIENCY = '2762071195'
    SWING_SPEED = '2837207746'
    CHARGE_TIME = '2961396640'
    MOBILITY = '2996146975'
    BOOST = '3017642079'
    POWER_BONUS = '3289069874'
    SOLAR_COST = '3344745325'
    ZOOM = '3555269338'
    ANY_ENERGY_TYPE_COST = '3578062600'
    PRECISION_DAMAGE = '3597844532'
    BLAST_RADIUS = '3614673599'
    ARC_ENERGY_CAPACITY = '3625423501'
    ARC_COST = '3779394102'
    MAGAZINE = '3871231066'
    DEFENSE = '3897883278'
    MOVE_SPEED = '3907551967'
    ADS_TIME = '3988418950'
    IMPACT = '4043523819'
    RELOAD_SPEED = '4188031367'
    STRENGTH = '4244567218'
    ROUNDS_PER_MINUTE = '4284893193'
    VOID_ENERGY_CAPACITY = '16120457'
    INTELLECT = '144602215'
    STABILITY = '155624089'
    DEFENSE = '209426660'
    DURABILITY = '360359141'
    RESILIENCE = '392767087'
    DRAW_TIME = '447667954'
    AMMO_CAPACITY = '925767036'
    HANDLING = '943549884'
    RANGE = '1240592695'
    AIM_ASSISTANCE = '1345609583'
    ATTACK = '1480404414'
    SPEED = '1501155019'
    HEROIC_RESISTANCE = '1546607977'
    ARC_DAMAGE_RESISTANCE = '1546607978'
    SOLAR_DAMAGE_RESISTANCE = '1546607979'
    VOID_DAMAGE_RESISTANCE = '1546607980'
    ACCURACY = '1591432999'
    DISCIPLINE = '1735777505'
    INVENTORY_SIZE = '1931675084'
    POWER = '1935470627'
    RECOVERY = '1943323491'
    SOLAR_ENERGY_CAPACITY = '2018193158'


class BucketEnum:
    ENERGY_WEAPONS = 2465295065
    UPGRADE_POINT = 2689798304
    STRANGE_COIN = 2689798305
    GLIMMER = 2689798308
    LEGENDARY_SHARDS = 2689798309
    SILVER = 2689798310
    BRIGHT_DUST = 2689798311
    SHADERS = 2973005342
    EMOTES = 3054419239
    MESSAGES = 3161908920
    SUBCLASS = 3284755031
    MODIFICATIONS = 3313201758
    HELMET = 3448274439
    GAUNTLET = 3551918588
    FINISHERS = 3683254069
    MATERIALS = 3865314626
    GHOST = 4023194814
    EMBLEMS = 4274335291
    CLAN_BANNERS = 4292445962
    CHEST_ARMOR = 14239492
    SHADERS = 18606351
    LEG_ARMOR = 20886954
    VAULT = 138197802
    LOST_ITEMS = 215593132
    SHIPS = 284967655
    ENGRAMS = 375726501
    POWER_WEAPONS = 953998645
    EMOTES = 1107761855
    AURAS = 1269569095
    QUESTS = 1345459588
    SPECIAL_ORDERS = 1367666825
    CONSUMABLES = 1469714392
    KINETIC_WEAPONS = 1498876634
    SEASONAL_ARTIFACT = 1506418338
    CLASS_ARMOR = 158578786