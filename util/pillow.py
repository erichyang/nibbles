import io
import os
import requests
import discord
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw

from util import characters
from util.udb import UserDatabase


class Pillow(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.title_font = ImageFont.truetype('./img/fonts/Tuesday Jingle.ttf',
                                             160)
        self.subtitle_font = ImageFont.truetype(
            './img/fonts/Tuesday Jingle.ttf', 120)
        self.body_font = ImageFont.truetype('./img/fonts/ACT.regular.ttf', 100)
        self.hand_font = ImageFont.truetype('./img/fonts/GHMS.ttf', 50)
        self.udb = UserDatabase(self.client)
        self.char_lib = characters.Characters(client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Pillow online')

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url and os.path.exists(
                f'./img/pfp/{before.id}.jpg'):
            os.remove(f'./img/pfp/{before.id}.jpg')

    async def generate_profile(self,
                               ctx,
                               user,
                               birthday='N/A',
                               prim_char=None):
        bg = Image.open('./img/backgrounds/profile_bg.jpg').convert('RGBA')
        response = requests.get(user.avatar_url)
        pfp = Image.open(io.BytesIO(response.content)).resize(
            (536, 536)).convert('RGBA')
        pfp_border = Image.open('./img/profile_border.png').resize((580, 580))
        bg.paste(pfp, (100, 100), mask=pfp)
        bg.paste(pfp_border, (80, 80), mask=pfp_border)

        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)

        overlay = Image.new('RGBA', bg.size, tint_color + (0, ))
        draw = ImageDraw.Draw(
            overlay)  # Create a context for drawing things on it.
        draw.rectangle(((660, 240), (1820, 1060)),
                       fill=tint_color + (opacity, ))

        user_info = self.udb.find_user(db='users', user=str(user.id))

        if user_info[4] == '' or user_info[4] is None:
            desc = 'This user has not set a description yet.'
        else:
            desc = user_info[4]
        if len(desc) > 450:
            desc = desc[:450]

        count = 13
        for i in range(len(desc)):
            if desc[i:i + 1] == '\n':
                count = 0
            elif count >= 45 and desc[i] == ' ':
                desc = desc[:i] + '\n' + desc[i + 1:]
                count = 0
            else:
                count += 1

        description = f'Description: {desc}'
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        if user.nick is None:
            name = user.display_name.upper()
        else:
            name = user.nick.upper()
        txt.text((700, 100),
                 name + "'s PROFILE", (18, 136, 196),
                 font=self.title_font)
        txt.text((695, 95),
                 name + "'s PROFILE", (199, 236, 255),
                 font=self.title_font)
        txt.text((680, 250), description, (0, 0, 0), font=self.body_font)
        txt.text((680, 900),
                 f'Exp: {user_info[1]}', (0, 0, 0),
                 font=self.body_font)
        txt.text((980, 900),
                 f'Nom noms: {user_info[2]}', (0, 0, 0),
                 font=self.body_font)
        txt.text((1480, 900),
                 f'Birthday: {birthday}', (0, 0, 0),
                 font=self.body_font)

        if prim_char is not None:
            portrait = Image.open(
                f'./img/char_portrait/Character_{prim_char[0].replace(" ", "+")}_Portrait.png')
            bg.paste(portrait, (400, 600), mask=portrait)
            level = self.char_lib.level_calc(prim_char[1])[0]
            char_info = self.char_lib.find_character(char_name=prim_char[0])
            char_desc = f'Name: {prim_char[0]}\nConstellation: {prim_char[2]}\nLevel: {level}\n' \
                        f'Attack: {int(char_info[3] + char_info[5] * level)}\n' \
                        f'Health: {int(char_info[4] + char_info[6] * level)}\n'
            txt.text((50, 650), char_desc, (0, 0, 0), font=self.body_font)

        bg = Image.alpha_composite(bg, overlay)
        bg = Image.alpha_composite(bg, text_layer)

        with io.BytesIO() as image_binary:
            bg.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(
                file=discord.File(fp=image_binary, filename='profile.png'))

    def generate_banner(self, five, fours):
        bg = Image.open('./img/backgrounds/banner_bg.png').convert('RGBA')
        five_portrait = Image.open(
            f'./img/char_portrait/Character_{five.replace(" ", "+")}_Portrait.png').resize(
                (360, 600))
        four_portrait = [
            Image.open(f'./img/char_portrait/Character_{fours[0].replace(" ", "+")}_Portrait.png'
                       ).resize((360, 600)),
            Image.open(f'./img/char_portrait/Character_{fours[1].replace(" ", "+")}_Portrait.png'
                       ).resize((360, 600)),
            Image.open(f'./img/char_portrait/Character_{fours[2].replace(" ", "+")}_Portrait.png'
                       ).resize((360, 600))
        ]
        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)
        overlay = Image.new('RGBA', bg.size, tint_color + (0, ))
        draw = ImageDraw.Draw(overlay)
        for i in range(4):
            draw.rectangle(
                ((192 + i * 384, 190), (192 + (i + 1) * 384 - 24, 190 + 700)),
                outline=(255, 255, 255))
            draw.rectangle(
                ((192 + i * 384, 190), (192 + (i + 1) * 384 - 24, 190 + 700)),
                fill=(tint_color + (opacity, )))

        bg = Image.alpha_composite(bg, overlay)
        bg.paste(five_portrait, (192, 250), mask=five_portrait)
        for i in range(3):
            bg.paste(four_portrait[i], (192 + (i + 1) * 384, 250),
                     mask=four_portrait[i])
        # text time
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((420, 50),
                 "Today's Banner Rotation", (255, 209, 248),
                 font=self.title_font)
        txt.text((415, 45),
                 "Today's Banner Rotation", (255, 255, 255),
                 font=self.title_font)
        txt.text((200, 190), five, (87, 125, 194), font=self.subtitle_font)
        for i in range(3):
            txt.text(((584 + i * 384), 190),
                     fours[i], (87, 125, 194),
                     font=self.subtitle_font)

        bg = Image.alpha_composite(bg, text_layer)
        bg.save('./img/banner.png')

    async def generate_wishes(self, ctx, results):
        bg = Image.open('./img/backgrounds/wishes_bg.png').convert('RGBA')
        portraits = []
        xp = [0, 0, 0]

        char = 0
        for item in results:
            if 'book' in item:
                if item == 'purple_book':
                    xp[0] += 1
                elif item == 'blue_book':
                    xp[1] += 1
                else:
                    xp[2] += 1
            else:
                portraits.append(
                    Image.open(
                        f'./img/char_portrait/Character_{item.replace(" ", "+")}_Portrait.png').
                    resize((390, 650)))
                char += 1
        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)
        overlay = Image.new('RGBA', bg.size, tint_color + (0, ))
        draw = ImageDraw.Draw(overlay)
        for i in range(char):
            draw.rectangle(
                ((96 + i * 360, 265), (96 + (i + 1) * 360 - 12, 265 + 600)),
                outline=(255, 255, 255))
            draw.rectangle(
                ((96 + i * 360, 265), (96 + (i + 1) * 360 - 12, 265 + 600)),
                fill=tint_color + (opacity, ))

        bg = Image.alpha_composite(bg, overlay)
        for i in range(char):
            bg.paste(portraits[i], (81 + i * 360, 245), mask=portraits[i])
        purple = Image.open('./img/books/purple_book.png')
        blue = Image.open('./img/books/blue_book.png')
        green = Image.open('./img/books/green_book.png')
        bg.paste(purple, (100 + char * 360, 450), mask=purple)
        bg.paste(blue, (300 + char * 360, 450), mask=blue)
        bg.paste(green, (500 + char * 360, 450), mask=green)
        # text time
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((600, 50),
                 "Summon Results", (255, 209, 248),
                 font=self.title_font)
        txt.text((595, 45),
                 "Summon Results", (255, 255, 255),
                 font=self.title_font)
        txt.text((96 + char * 360, 500),
                 'XP books: ', (255, 255, 255),
                 font=self.subtitle_font)
        txt.text((150 + char * 360, 600),
                 str(xp[0]), (255, 255, 255),
                 font=self.body_font)
        txt.text((400 + char * 360, 600),
                 str(xp[1]), (255, 255, 255),
                 font=self.body_font)
        txt.text((650 + char * 360, 600),
                 str(xp[2]), (255, 255, 255),
                 font=self.body_font)
        bg = Image.alpha_composite(bg, text_layer)
        with io.BytesIO() as image_binary:
            bg.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename='results.png'))

    def generate_lb(self, ranks, names, pts):
        bg = Image.open('./img/backgrounds/leaderboard.png').convert('RGBA')

        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((100, 350), ranks, (255, 255, 255), font=self.hand_font)
        txt.text((200, 350), names, (255, 255, 255), font=self.hand_font)
        txt.text((850, 350), pts, (255, 255, 255), font=self.hand_font)
        bg = Image.alpha_composite(bg, text_layer)
        with io.BytesIO() as image_binary:
            bg.save(image_binary, 'PNG')
            image_binary.seek(0)
            return discord.File(fp=image_binary, filename='leaderboard.png')


def setup(client):
    client.add_cog(Pillow(client))
