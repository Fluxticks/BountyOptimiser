from discord.ext import commands
import discord
from util import makeLogger

discordToken = 'NzA2ODkwNTgzNDQ0MjkxNjI0.XrG6rA.gMIioU79h9hc92hVEJ61fduFx0E'
bot = commands.Bot(command_prefix=commands.when_mentioned_or('['), description="Supercharge your bounty farming with this bot!")
logger = makeLogger('bot')

#token = open('token.txt', 'r').read()

@bot.event
async def on_ready():
    """Runs when the bot has successfully logged in
    """
    logger.info('Logging In')
    logger.info(f'\t name: {bot.user.name}')
    logger.info(f'\t id: {bot.user.id}')
    logger.info(f'\t guilds: {len(bot.guilds)}')

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx):
    a = ctx.message.author
    if a.id == 244050529271939073:
        logger.warn('Reloading bot. You will need to restart, this is temporary')
        await ctx.send('Hello Fluxticks :) Remember to restart soon')
        bot.reload_extension('handler')
        logger.info('Done Reloading')

bot.remove_command('help')
bot.load_extension('handler')
bot.run(discordToken)







