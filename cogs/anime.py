import asyncio
import math
import random
import time
from functools import lru_cache

import discord
from discord.ext.commands import CommandInvokeError, BadArgument
from jikanpy import Jikan, APIException

from tinydb import TinyDB, Query
from discord.ext import commands, tasks
from util import server_manage, udb
from util.idb import quick_sort


def anime_db(user_id, item):
    # item is either anime_list, wish_list, inventory
    with TinyDB('./data/anime.json') as db:
        doc = db.search(Query().user == user_id)
        if len(doc) > 0:
            return doc[0].get(item)
        else:
            return doc


def anime_inventory_add(user_id, character_id):
    # relation friendship - True, romance - False
    profile_exists(user_id)
    with TinyDB('./data/anime.json') as db:
        inventory = db.search(Query().user == user_id)[0]['inventory']
        inventory.append({'mal_id': character_id, 'affection': 0, 'relationship': None})
        db.update({'inventory': inventory}, Query().user == user_id)


def profile_exists(user_id):
    with TinyDB('./data/anime.json') as db:
        profile = db.search(Query().user == user_id)
        if len(profile) == 0:
            db.insert({'user': user_id, 'anime_list': [], 'wishlist': [], 'inventory': []})
            return False
        return True


class Anime(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.udb = udb.UserDatabase(client)
        self.server = server_manage.ServerManage(client)
        self.cache = {}
        self.jikan = Jikan()
        self.interactions = []
        self.genshin_db = client.get_cog('Characters')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Anime online')
        self.anime_char_timer.start()

    @lru_cache(maxsize=256)
    def mal_character(self, mal_id):
        try:
            char = self.jikan.character(mal_id)
        except APIException:
            time.sleep(1)
            char = self.jikan.character(mal_id)
        time.sleep(0.5)
        return char

    @tasks.loop(minutes=45)
    async def anime_char_timer(self):
        for channel in await self.server.anime_channels():
            await self.anime_char_spawn(channel)
        self.interactions = []

    async def anime_char_spawn(self, channel):
        await asyncio.sleep(random.randint(0, 900))
        chatters = []
        async for message in channel.history(limit=100):
            if message.author.id not in chatters:
                chatters.append(message.author.id)
        animes = []
        for user_id in chatters:
            doc = anime_db(user_id, 'anime_list')
            if len(doc) == 0:
                continue
            for anime_id in doc:
                if anime_id not in animes:
                    animes.append(anime_id)
        image = 'https://cdn.myanimelist.net/images/questionmark_23.gif?s=f7dcbc4a4603d18356d3dfef8abd655c'
        anime = {}
        char = {}
        c_id = -1
        await asyncio.sleep(20)
        while 'questionmark_23' in image or 'apple-touch-icon' in image:
            try:
                if len(animes) < 10:
                    return
                anime = self.jikan.anime(random.choice(animes))
                c_id = random.choice(self.jikan.anime(anime['mal_id'], extension='characters_staff')['characters'])[
                    'mal_id']
                char = self.mal_character(c_id)
            except APIException:
                time.sleep(1)
                anime = self.jikan.anime(random.choice(animes))
                c_id = random.choice(self.jikan.anime(anime['mal_id'], extension='characters_staff')['characters'])[
                    'mal_id']
                char = self.mal_character(c_id)
            image = char['image_url']

        price = math.log2(anime['members'] + 1) * 50
        price += math.log2(char['member_favorites'] + 1) * 400
        price = int(price)
        desc = f"{anime['title']}\nAnime Members: {anime['members']}\nFavorite by {char['member_favorites']}\n" \
               f"React 🍪 to claim for {price} nom noms!"
        embed = discord.Embed(title=f"**{char['name']}**", description=desc)
        embed.set_image(url=image)
        embed.set_footer(text=str(c_id))
        msg = await channel.send(embed=embed, delete_after=600)
        await msg.add_reaction('🍪')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot and reaction.message.author.bot and len(reaction.message.embeds) == 1:
            profile_exists(user_id=user.id)
            if reaction.emoji == '🍪':
                embed = reaction.message.embeds[0]
                channel = reaction.message.channel
                cost = int(embed.description.split(' ')[-3])
                if self.udb.find_user('users', str(user.id), 'bal')[0] < cost:
                    return
                try:
                    inventory = anime_db(user.id, 'inventory')
                except IndexError:
                    return
                mal_id = int(embed.footer.text)
                if any(char['mal_id'] == mal_id for char in inventory):
                    await self.udb.update('users', 'bal', f'+4000', user.id)
                    await channel.send(f'**{user.name}** earned 4000 🍪s!')
                    return

                await reaction.message.delete()
                await self.udb.update('users', 'bal', f'-{cost}', user.id)

                anime_inventory_add(user.id, mal_id)
                await channel.send(f'**{user.name}** claimed {reaction.message.embeds[0].title} for {cost} nom noms!')
            elif reaction.emoji == '⬅' or reaction.emoji == '➡':
                sect = int(reaction.message.embeds[0].footer.text)
                if reaction.emoji == '⬅':
                    sect -= 1 if sect > 0 else 0
                else:
                    sect += 1
                await reaction.message.edit(embed=await self.main_inventory_view(user, sect))
            elif reaction.emoji == '👋':
                c_id = int(reaction.message.embeds[0].footer.text)
                inventory = anime_db(user.id, 'inventory')
                char = None
                index = -1
                for i, item in enumerate(inventory):
                    if item['mal_id'] == int(c_id):
                        char = item
                        index = i
                        break
                if user.id not in self.interactions and char is not None:
                    gain = random.randint(10, 100)
                    await reaction.message.channel.send(f'You gained {gain} affection!')
                    self.interactions.append(user.id)
                    with TinyDB('./data/anime.json') as db:
                        char['affection'] += gain
                        inventory[index] = char
                        db.update({'inventory': inventory}, Query().user == user.id)
            elif reaction.emoji == '🙌' or reaction.emoji == '💞':
                inventory = anime_db(user.id, 'inventory')
                c_id = int(reaction.message.embeds[0].footer.text)
                char = None
                index = -1
                for i, item in enumerate(inventory):
                    if item['mal_id'] == int(c_id):
                        char = item
                        index = i
                        break

                if char is not None and char['relationship'] is None:
                    if reaction.emoji == '💞':
                        char['relationship'] = False
                    elif reaction.emoji == '🙌':
                        char['relationship'] = True
                    inventory[index] = char
                    with TinyDB('./data/anime.json') as db:
                        db.update({'inventory': inventory}, Query().user == user.id)
                    await reaction.message.channel.send('Successfully set!')

    @commands.command(description='your list of animes that you would like to appear\n.anime_list', aliases=['al'])
    async def anime_list(self, ctx):
        if not profile_exists(ctx.author.id):
            await ctx.send('Your anime list is currently empty!')
            return
        anime_ids = anime_db(ctx.author.id, 'anime_list')
        desc = 'When an anime character randomly appears, your list of animes will have a chance to appear!'
        embed = discord.Embed(title=f'My Animes {len(anime_ids)}/10', description=desc)
        al = []
        for item in anime_ids:
            al.append(self.jikan.anime(item))

        for anime in al:
            value = f"[Title] {anime['title']}" \
                    f"\n[EN Title] {anime['title_english']}" \
                    f"\n[MyAnimeList]({anime['url']})"
            embed.add_field(name=anime['mal_id'], value=value)

        await ctx.send(embed=embed)

    @commands.command(description='add to your list of animes\n.anime_list_add 14813', aliases=['ala'])
    async def anime_list_add(self, ctx, anime_id: int):
        try:
            self.jikan.anime(anime_id)
        except APIException:
            await ctx.send('This anime doesn\'t exist!')
            return
        profile_exists(ctx.author.id)
        current = anime_db(ctx.author.id, 'anime_list')
        if len(current) >= 10:
            await ctx.send('Your anime list is full!')
            return
        if anime_id in current:
            await ctx.send('You already have this anime in your list!')
            return
        with TinyDB('./data/anime.json') as db:
            current.append(anime_id)
            db.update({'anime_list': current}, Query().user == ctx.author.id)
        await ctx.send('Successfully added!')

    @commands.command(description='remove from your list of animes\n.anime_list_remove 11757', aliases=['alr'])
    async def anime_list_remove(self, ctx, anime_id: int):
        current = anime_db(ctx.author.id, 'anime_list')
        if current is None:
            await ctx.end("You do not have any animes in your list yet")
            return
        if anime_id in current:
            current.remove(anime_id)
            with TinyDB('./data/anime.json') as db:
                db.update({'anime_list': current}, Query().user == ctx.author.id)
            await ctx.send('Anime removed successfully')
        else:
            await ctx.send('This anime is not in your list')

    @commands.command(description='look up an anime either by name or ID\n.anime_search 14813; .as SNAFU',
                      aliases=['as'])
    async def anime_search(self, ctx, *, anime_search):
        if anime_search.isdigit():
            try:
                anime = self.jikan.anime(anime_search)
            except APIException:
                await ctx.send('This anime doesn\'t exist!')
                return
            desc = f"\n[Title] {anime['title']}\n[EN Title] {anime['title_english']}\n[Score] {anime['score']}\n" \
                   f"[Members] {anime['members']}\n[Rank] {anime['rank']}\n[MyAnimeList]({anime['url']})\n" \
                   f"[List of Characters]({anime['url']}/characters)"
            embed = discord.Embed(title=anime_search, description=desc)
            if anime['url'] is not None:
                embed.set_image(url=anime['image_url'])
            await ctx.send(embed=embed)
        else:
            anime_results = self.jikan.search('anime', anime_search)
            content = "Anime Search Results - use .as <anime ID> for a more detailed view of each Anime!\n"
            count = 0
            for anime in anime_results['results']:
                count += 1
                if count == 11:
                    break
                content += f"\n[**{anime['mal_id']}**] {anime['title']}"
            await ctx.send(content)

    async def main_inventory_view(self, user, sect):
        if not profile_exists(user.id):
            return
        inventory = anime_db(user.id, 'inventory')
        quick_sort(inventory, 0, len(inventory) - 1, lambda x, y: x['affection'] < y['affection'])
        if (len(inventory) / 15) < sect:
            sect -= 1
        cl = []
        start_index = 15 * sect
        end_index = 15 + 15 * sect
        if end_index >= len(inventory):
            end_index = len(inventory)
        for item in inventory[start_index:end_index]:
            character = self.mal_character(item['mal_id'])
            cl.append((character['mal_id'], character['name'], item['affection']))
        desc = ""
        for tup in cl:
            desc += f"[{tup[0]}] {tup[1]} - {tup[2]}♥\n"

        embed = discord.Embed(title=f"{user.name}'s adventure party", description=desc, footer=str(sect))
        embed.set_footer(text=str(sect))
        return embed

    @commands.command(description='a list of all the anime characters you own!\n.anime_inventory', aliases=['ainv'])
    async def anime_inventory(self, ctx):
        embed = await self.main_inventory_view(ctx.author, 0)
        if embed is None:
            await ctx.send('Your inventory is currently empty!')
        else:
            msg = await ctx.send(embed=embed)
            await msg.add_reaction('⬅')
            await msg.add_reaction('➡')

    @commands.command(aliases=['achar'], description='Look up an anime character by name or ID\n'
                                                     '.anime_character Kanna Kamui; .achar 170466')
    async def anime_character(self, ctx, *, character_id):
        if not character_id.isdigit():
            anime_results = self.jikan.search('character', character_id)
            content = "Anime Character Search Results - use .achar <MAL ID> for a detailed view of this character!\n"
            count = 0
            for anime in anime_results['results']:
                count += 1
                if count == 11:
                    break
                content += f"\n[**{anime['mal_id']}**] {anime['name']}"
            await ctx.send(content)
            return
        try:
            character = self.mal_character(character_id)
        except APIException:
            await ctx.send('Sorry, nibbles cannot find this character right now, pls try again later?')
            return

        about_var = []
        if 'Age: ' in character['about']:
            index = character['about'].find('Age: ')
            about_var.append(character['about'][index:].partition('\\n')[0])
        if 'Birthday: ' in character['about']:
            index = character['about'].find('Birthday: ')
            about_var.append(character['about'][index:].partition('\\n')[0])
        if 'Height: ' in character['about']:
            index = character['about'].find('Height: ')
            about_var.append(character['about'][index:].partition('\\n')[0])
        if 'Weight: ' in character['about']:
            index = character['about'].find('Weight: ')
            about_var.append(character['about'][index:].partition('\\n')[0])
        if 'Affiliation: ' in character['about']:
            index = character['about'].find('Affiliation: ')
            about_var.append(character['about'][index:].partition('\\n')[0])
        about = ''
        for var in about_var:
            about += var + '\n'
        ag = character['animeography']
        animes = f"[{ag[0]['mal_id']}] {ag[0]['name']}"
        for anime in ag[1:-1]:
            animes += f', [{anime["mal_id"]}] {anime["name"]}'
        if len(character['animeography']) > 1:
            animes += f" and [{ag[-1]['mal_id']}] {ag[-1]['name']}"

        desc = f"Favorite by {character['member_favorites']} members\n{about}\n\nAppears in: {animes}"
        embed = discord.Embed(title=f"**{character['name']}** {character['name_kanji']}", description=desc)
        inventory = anime_db(ctx.author.id, 'inventory')
        char = next((x for x in inventory if x['mal_id'] == int(character_id)), None)
        if char is not None:
            lvl = self.genshin_db.level_calc(char['affection'] * 1000)[0]
            relationship = 'strangers'
            if char['relationship'] is None or lvl < 60:
                if lvl >= 40:
                    relationship = 'casual friends'
                elif lvl >= 20:
                    relationship = 'acquaintances'
            elif char['relationship']:
                if lvl >= 70:
                    relationship = 'besties'
                else:
                    relationship = 'close friends'
            elif not char['relationship']:
                if lvl >= 90:
                    relationship = 'married'
                elif lvl >= 80:
                    relationship = 'engaged'
                elif lvl >= 70:
                    relationship = 'dating'
                else:
                    relationship = 'interested'
            title = 'Affection'
            if char['relationship'] is None:
                pass
            elif char['relationship']:
                title = 'Friendship'
            else:
                title = 'Romance'
            embed.add_field(name=f'{title} - {relationship}', value=f"{char['affection']}♥")
            if char['relationship'] is None:
                embed.add_field(name='React 🙌 or 💞', value='to choose between friendship or romance, respectively. '
                                'Choose wisely, you only get this choice once per character!')
            # multiplier of 1000 for converting between genshin and anime levels
            # 0 - strangers
            # 20 - acquaintances
            # 40 - casual friends
            # friendship
            # 60 - close friends
            # 70 - besties
            # romance
            # 60 - interested
            # 70 - dating
            # 80 - engaged
            # 90 - married
        embed.set_image(url=character['image_url'])
        embed.set_footer(text=character_id)
        msg = await ctx.send(embed=embed)
        if char is not None:
            await msg.add_reaction('👋')
        if char['relationship'] is None:
            await msg.add_reaction('🙌')
            await msg.add_reaction('💞')

    @anime_inventory.error
    @anime_list.error
    @anime_list_add.error
    @anime_search.error
    @anime_inventory.error
    @anime_character.error
    async def rate_limit_error(self, ctx, error):
        if isinstance(error, CommandInvokeError) and error.original.error_json['type'] == 'RateLimitException':
            await ctx.send('Rate limited to not offend MAL, please try again in 30s <:KaiCry:778399319086596106>')
        elif isinstance(error, ValueError) or isinstance(error, BadArgument):
            await ctx.send('<:HuTaoRip:833535556759191572> did you gib nibbles an ID?')
        else:
            print(error)


def setup(client):
    client.add_cog(Anime(client))
