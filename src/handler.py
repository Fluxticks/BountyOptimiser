import discord
from discord.ext import commands
from main import setup as setup_bounty
from Exceptions import DiscordError
from util import makeLogger
import sys
import logging
from util import embed_message as embed
from bs4 import BeautifulSoup
import requests

logger = makeLogger('handler')

global handler

def setup(bot):
    global handler
    logger.debug('Adding handler cog')
    handler = Handler(bot)
    bot.add_cog(handler)


def teardown(bot):
    global handler
    del handler._bounty
    logger.info('Unloading handler')


'''async def makeMessage(data):
    logger.info('Making embeded message!')
    message = discord.Embed(title="Bounty Optimser")

    name = data.get('name')
    member = data.get('id')
    platform = data.get('type')
    data = data.get('data').get('2305843009301295844')
    url = f'https://www.bungie.net/en/Profile/{platform}/{member}/'
    icon = getSoup(url)

    message.set_author(name=name + " | " + str(member) + " | " + str(platform), icon_url=icon)
    for index, bucket in enumerate(data):
        logger.debug('Making section for bucket: %s', index)
        message.add_field(name=f'__**Bucket {index + 1}:**__',
                          value="**-----------------------------------------------------------------------------**",
                          inline=False)
        getLoadout(message, bucket.identifiers)
        message.add_field(name='__Objectives__', value=str(bucket), inline=False)
        for bounty in bucket.bounties:
            logger.debug('Adding bounty with: %s and %s', bounty.title, bounty.description)
            message.add_field(name="**" + bounty.title + "**", value=bounty.description, inline=True)

    logger.info('Finished making embeded message')
    return message'''

async def makeMessages(ctx, data):
    logger.info('Making embeded message!')

    name = data.get('name')
    member = data.get('id')
    platform = data.get('type')
    buckets = data.get('data')
    url = f'https://www.bungie.net/en/Profile/{platform}/{member}/'
    icon = getSoup(url)

    author = name + " | " + str(member) + " | " + str(platform)

    characters = data.get('characters')
    keys = list(characters.keys())

    for character in keys:
        if len(buckets.get(character)) > 0:
            banner = discord.Embed(title=characters.get(character).get('gender')+' '+characters.get(character).get('race')+' '+characters.get(character).get('class')+' | '+characters.get(character).get('light'))
            banner.set_author(name=author,icon_url=icon)
            banner.set_image(url='https://bungie.net'+characters.get(character).get('emblem'))
            await ctx.send(embed=banner)
            for index,bucket in enumerate(buckets.get(character)):
                message = discord.Embed(title="Bucket " + str(index + 1), description=makeDescription(bucket.identifiers))
                message.set_author(name=author,icon_url=icon)
                message.set_footer(text="Sumbit bugs to: https://github.com/Fluxticks/BountyOptimiser/issues")
                getLoadout(message, bucket.identifiers)
                for bounty in bucket.bounties:
                    message.add_field(name="**"+bounty.title+"**", value=bounty.description, inline=True)
                await ctx.send(embed=message)


def getLoadout(message, identifiers):
    string = ""

    if 'kinetic' in identifiers:
        string += 'Kinetic: ' + identifiers.get('kinetic')
    if 'energy' in identifiers:
        string += '\nEnergy: ' + identifiers.get('energy')
    if 'power' in identifiers:
        string += '\nPower: ' + identifiers.get('power')

    logger.debug('Made loadout string: %s', string)

    if string != "":
        if string.startswith('\n', 0, 2):
            string = string[2:]
        message.add_field(name='__Loadout__', value=string, inline=False)

def makeDescription(data):
    description = ""
    if data.get('location'):
        location = 'On ' + data.get('location')[0]
        description += location
    if data.get('activity'):
        activity = 'in ' + data.get('activity')[0]
        if len(data.get('activity')) != 1:
            for i in range(len(data.get('activity')) - 1):
                activity += ', ' + data.get('activity')[i]
            activity += ' or ' + data.get('activity')[-1]
        description += " "+activity
    if data.get('enemy'):
        enemy = 'defeat ' + data.get('enemy')[0]
        if len(data.get('enemy')) != 1:
            for i in range(len(data.get('enemy')) - 1):
                enemy += ', ' + data.get('enemy')[i]
            enemy += ' and ' + data.get('enemy')[-1]
        description += " " + enemy
    if data.get('ability'):
        ability = '. Use ' + data.get('ability')[0]
        if len(data.get('ability')) != 1:
            for i in range(len(data.get('ability')) - 1):
                ability += ', ' + data.get('ability')[i]
            ability += ' or ' + data.get('ability')[-1]
        description += ability
    if data.get('ability') and data.get('element'):
        element = f'({data.get("element")[0]})'
        description += element

    return description



def getSoup(url):
    response = BeautifulSoup(requests.get(url).text, 'html.parser')
    data = response.find("img", {"class": "user-avatar"})
    logger.debug('Got response and image: %s', data['src'])
    return 'https://bungie.net' + data['src']


class Handler(commands.Cog):

    def __init__(self, bot):
        self._bot = bot
        self._bounty = setup_bounty()

    @commands.group(name='help',invoke_without_command=True)
    async def do_help(self,ctx):
        text = """Main command: {0}optimise\n Extra commands:{0}help private, {0}help many, {0}help optimise\n
        1. Ensure your bungie.net profile is public, if you are unsure: !help private\n
        2. There may be many people with the same name as you, for assistance: {0}help many\n
        3. If you encounter any bugs or issues, report them here: https://github.com/Fluxticks/BountyOptimiser/issues
            Please ensure to include your discord tag and the command with the arguments you included.
               """.format(ctx.prefix)
        await ctx.send(embed=embed('Help', description=text, colour=0xFF00FF))

    @do_help.command(name='private')
    async def do_private(self,ctx):
        text = """This bot finds your bounties using the public data of your inventory.
        To make your inventory public, on Bungie.Net go to Your Profile -> Settings -> Privacy and Check "Show my Progression" and "Show my non-equipped Inventory".
        Once this is done, there may be some time while Bungie updates the API with your settings, so please be patient.
        """
        await ctx.send(embed=embed('Help Private', description=text, colour=0xFF00FF))

    @do_help.command(name='many')
    async def do_many(self,ctx):
        text = """Names on Bungie.net are not unique, rather each account as a platformID and a memberID.
        1) If you know which account in the list is yours, use -i after your name and then the number in the list of your account
        2) If you don't know which is yours, use the -m and -t flags to specify the memberID and platformID respectively\n
            2a) To find your IDs use the search function on bungie.net and search your name.
            2b) Select "Destiny Players" and find your account.
            2c) In the url get the single digit number is your platformID and the long number is your memberID\n
            __example:__
            https://www.bungie.net/en/Profile/3/4611686018467260457/Fuxticks 
            would get: platformID: 3 | memberID: 4611686018467260457
            and the command: !optimise -m 4611686018467260457 -t 3
        """
        await ctx.send(embed=embed('Help Many', description=text,colour=0xFF00FF))

    @do_help.command(name='optimise')
    async def help_opt(self,ctx):
        text = """To run the bot use the command "optimise" followed by one of the following options:
        1) -n <your name> [-i <index of your account in the list if many>]
        2) -m <memberID> -t <platformID>
        """
        await ctx.send(embed=embed('Help Optimse', description=text, colour=0xFF00FF))

    @commands.command()
    async def optimise(self, ctx, *args):
        """
        Will give you an optimised group of bounties that you currently have!

        Args:
            -n: Your display name
            -i: If there are multiple people with similar display names -i indicates which one in the list (starts from 0)
            -m: Used in-joint with -t, -m is used to define your memberId (can be found using !info)
            -t: Your memberType (platformId), is required when using your memberId
        """

        # -n -> display name
        # -i -> index starting from 1 (ie remove 1)
        # -m -> memberId
        # -t -> memberType

        displayName = None
        index = None
        member = None
        platform = None

        if len(args) > 4 or len(args) == 0:
            await ctx.send(
                embed=embed('Invalid argument count!', description=f'Use "{ctx.prefix}help optimise" for help', colour='red'))
            return

        if '-n' in args:

            displayName = args[args.index('-n') + 1]

            if '-i' in args:
                index = args[args.index('-i') + 1]
                index = int(index) - 1

        elif '-m' in args:

            member = args[args.index('-m') + 1]

            if '-t' not in args:
                await ctx.send(embed=embed('Invalid Arguemnt Configuration!',
                                           description='To search using memberId, memberType is also required using the -t flag',
                                           colour='red'))
                return

            platform = args[args.index('-t') + 1]

        try:
            message = await ctx.send(embed=embed('Starting!', description='Please wait while we search your bounties!',colour='green'))
            data = self._bounty.performOptimisation(player=displayName, index=index, member=member, platform=platform)
            await makeMessages(ctx, data)
            await message.delete()
        except DiscordError as e:
            message = e.message
            await ctx.send(embed=embed('Oops...', description=message,
                                       footer='If you believe you typed everything in correctly, create a bug report on: https://github.com/Fluxticks/BountyOptimiser/issues making sure to include your discord handle and the command you tried to run.',
                                       colour='red'))
        except BaseException as ex:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            logger.error('(%s) %s', ex_type, ex_value)
            await ctx.send(embed=embed('Error!',
                                       description='There was an internal error while processing your request. Please report this bug here: https://github.com/Fluxticks/BountyOptimiser/issues making sure to include your discord handle, the command you tried to run and the error message\nError Message: '+ex_value,
                                       colour='red'))
