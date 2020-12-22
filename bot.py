import discord
import os
import random
from discord.ext import commands, tasks
from itertools import cycle

client = commands.Bot(command_prefix='.',
                      intents=discord.Intents(messages=True, guilds=True, reactions=True, members=True, presences=True))
status = cycle(['cookie nomming', 'sleeping', 'tail chasing', 'grooming'])

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
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("nibbles can't do anything because something is missing! <:ShibaNervous:703366029425901620>")


@client.event
async def on_member_update(prev, cur):

    if cur.activity is not None:
        role = discord.utils.get(cur.guild.roles, name=cur.activity.name)
        if role is not None:
            await cur.add_roles(role)
    else:
        await cur.remove_roles(discord.utils.get(prev.guild.roles, name='League of Legends'))
        await cur.remove_roles(discord.utils.get(prev.guild.roles, name='Genshin Impact'))
        await cur.remove_roles(discord.utils.get(prev.guild.roles, name='Minecraft'))
        await cur.remove_roles(discord.utils.get(prev.guild.roles, name='Far Cry 5'))
        await cur.remove_roles(discord.utils.get(prev.guild.roles, name='Ooblets'))


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        await message.channel.send("nom")
    else:
        await client.process_commands(message)

client.run('NzM2MDEzNjQ1MDQ1MzAxMzAx.XxooHw.lFN86LS_ZVA1aeQ_4gtL4irUp0U')
