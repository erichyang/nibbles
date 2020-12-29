import discord
import os
import random
from discord.ext import commands, tasks
from itertools import cycle

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True))
client.remove_command('help')

status = cycle(['cookie nomming', 'sleeping', 'tail chasing', 'grooming', 'being a ball of fluff'])

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.event
async def on_ready():
    change_status.start()
    print("Nibbles is awake!")


@tasks.loop(minutes=random.randrange(10, 45))
async def change_status():
    await client.change_presence(activity=discord.Streaming(name=next(status), url='https://twitch.tv/bitnoms'))


@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')


@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')


@client.event
async def on_member_join(member):
    await member.guild.get_channel(681149093858508834).send(f'Heyaa {member.name}, '
                                                            f'I\'m nibbles! <:kayaya:778399319803035699>')
    await member.add_roles(discord.utils.get(member.guild.roles, name='Comets'))
    await member.edit(nick=member.name.lower())


@client.event
async def on_member_remove(member):
    await member.guild.get_channel(681149093858508834).send(f'Bai bai {member.name} <:qiqi:781667748031103036>')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument) and ctx.message.content != '.help':
        await ctx.send("nibbles can't do anything because something is missing! <:ShibaNervous:703366029425901620>")


@client.event
async def on_member_update(prev, cur):
    games = ['League of Legends', 'Genshin Impact', 'Minecraft', 'Heroes of Hammerwatch', 'Ooblets', 'Spotify']

    if cur.activity is not None and cur.activity.name in games:
        role = discord.utils.get(cur.guild.roles, name=cur.activity.name)
        try:
            await cur.add_roles(role)
        except AttributeError:
            pass
        if prev.activity is not None and prev.activity.name in games:
            old = discord.utils.get(prev.roles, name=prev.activity.name)
            try:
                await prev.remove_roles(old)
            except AttributeError:
                pass
    else:
        try:
            for game in games:
                await cur.remove_roles(discord.utils.get(prev.guild.roles, name=game))
        except AttributeError:
            pass


@client.command()
async def help(ctx, command):
    embed_var = discord.Embed(title="Nibbles is here to help", color=0x8109e9)
    desc = {
        'choose': 'Nibbles helps you choose because you\'re too indecisive',
        'coin_flip': 'Flips a coin!',
        'poll': 'Nibbles helps you discover that other people are indecisive too',
        'purge': 'pew pew destroy messages'
    }
    if command is None:
        embed_var.add_field(name='choose', value=desc.get('choose'), inline=False)
        embed_var.add_field(name='coin_flip', value=desc.get('coin_flip'), inline=False)
        embed_var.add_field(name='poll', value=desc.get('poll'), inline=False)
        embed_var.add_field(name='purge', value=desc.get('purge'), inline=False)
        embed_var.set_footer(text="ask for more help on specific commands by using .help <command>")
        await ctx.channel.send(embed=embed_var)
    else:
        example = {
            'choose': '.choose go to work, play video games, something else',
            'coin_flip': '.coin_flip',
            'poll': '.poll Do you like nibbles?',
            'purge': '.purge 5'
        }
        if desc.get(command, 'no such command') == 'no such command':
            await ctx.send('this command doesn\'t exist!')
        else:
            embed_var.add_field(name='Command name', value=command, inline=False)
            embed_var.add_field(name='Command description', value=desc.get(command, 'no such command'), inline=False)
            embed_var.add_field(name='Command usage', value=example.get(command, 'no such command'), inline=False)
            await ctx.channel.send(embed=embed_var)


@help.error
async def help_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await help(ctx, None)


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        await message.channel.send("nom")
    else:
        await client.process_commands(message)


client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.xsWixaBVaiRICZWhoP1A8x4StXc')
