import os

import discord
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw

from util.udb import UserDatabase


class Pillow(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.title_font = ImageFont.truetype('./img/Tuesday Jingle.ttf', 160)
        self.body_font = ImageFont.truetype('./img/act.regular.ttf', 100)
        self.udb = UserDatabase(self.client)

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Pillow online')

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url and os.path.exists(f'./img/{before.id}.jpg'):
            os.remove(f'./img/{before.id}.jpg')

    def generate_profile(self, user):
        bg = Image.open('./img/profile_bg.jpg').convert('RGBA')
        pfp = Image.open(f'./img/pfp/{user.id}.jpg').resize((536, 536))
        pfp_border = Image.open('./img/profile_border.png').resize((580, 580))
        bg.paste(pfp, (100, 100))
        bg.paste(pfp_border, (80, 80), mask=pfp_border)

        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)

        overlay = Image.new('RGBA', bg.size, tint_color + (0,))
        draw = ImageDraw.Draw(overlay)  # Create a context for drawing things on it.
        draw.rectangle(((660, 240), (1820, 1060)), fill=tint_color + (opacity,))

        user_info = self.udb.find_user(db='users', user=str(user.id))

        if user_info[4] == '' or user_info[4] is None:
            desc = 'This user has not set a description yet.'
        else:
            desc = user_info[4]
        if len(desc) > 450:
            desc = desc[:450]

        count = 13
        for i in range(len(desc)):
            if count >= 45 and desc[i] == ' ':
                desc = desc[:i] + '\n' + desc[i + 1:]
                count = 0
            else:
                count += 1

        description = f'Description: {desc}'
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((700, 100), user.nick.upper() + "'s PROFILE", (18, 136, 196), font=self.title_font)
        txt.text((695, 95), user.nick.upper() + "'s PROFILE", (199, 236, 255), font=self.title_font)
        txt.text((680, 250), description, (0, 0, 0), font=self.body_font)
        txt.text((680, 900), f'Exp: {user_info[1]}', (0, 0, 0), font=self.body_font)
        txt.text((1180, 900), f'Nom noms: {user_info[2]}', (0, 0, 0), font=self.body_font)
        bg = Image.alpha_composite(bg, overlay)
        bg = Image.alpha_composite(bg, text_layer)
        bg.save('./img/profile.png')

    def generate_banner(self, five, fours):
        bg = Image.open('./img/banner_bg.jpg').convert('RGBA')
        five_portrait = Image.open(f'./img/char_portrait/Character_{five}_Portrait.png')
        four_portrait = []
        four_portrait[0] = Image.open(f'./img/char_portrait/Character_{fours[0]}_Portrait.png')
        four_portrait[1] = Image.open(f'./img/char_portrait/Character_{fours[1]}_Portrait.png')
        four_portrait[2] = Image.open(f'./img/char_portrait/Character_{fours[2]}_Portrait.png')

        bg.save('./img/banner.png')


def setup(client):
    client.add_cog(Pillow(client))
