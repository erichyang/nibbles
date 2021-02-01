import os

from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw

from util.udb import UserDatabase


class Pillow(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.title_font = ImageFont.truetype('./img/Tuesday Jingle.ttf', 160)
        self.subtitle_font = ImageFont.truetype('./img/Tuesday Jingle.ttf', 120)
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
        bg = Image.open('./img/banner_bg.png').convert('RGBA')
        five_portrait = Image.open(f'./img/char_portrait/Character_{five}_Portrait.png').resize((360, 600))
        four_portrait = [Image.open(f'./img/char_portrait/Character_{fours[0]}_Portrait.png').resize((360, 600)),
                         Image.open(f'./img/char_portrait/Character_{fours[1]}_Portrait.png').resize((360, 600)),
                         Image.open(f'./img/char_portrait/Character_{fours[2]}_Portrait.png').resize((360, 600))]
        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)
        overlay = Image.new('RGBA', bg.size, tint_color + (0,))
        draw = ImageDraw.Draw(overlay)
        for i in range(4):
            draw.rectangle(((192 + i * 384, 190), (192 + (i + 1) * 384 - 24, 190 + 700)), outline=(255, 255, 255))
            draw.rectangle(((192 + i * 384, 190), (192 + (i + 1) * 384 - 24, 190 + 700)),
                           fill=(tint_color + (opacity,)))

        bg = Image.alpha_composite(bg, overlay)
        bg.paste(five_portrait, (192, 250), mask=five_portrait)
        for i in range(3):
            bg.paste(four_portrait[i], (192 + (i + 1) * 384, 250), mask=four_portrait[i])
        # text time
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((420, 50), "Today's Banner Rotation", (255, 209, 248), font=self.title_font)
        txt.text((415, 45), "Today's Banner Rotation", (255, 255, 255), font=self.title_font)
        txt.text((200, 190), five, (87, 125, 194), font=self.subtitle_font)
        for i in range(3):
            txt.text(((584 + i * 384), 190), fours[i], (87, 125, 194), font=self.subtitle_font)

        bg = Image.alpha_composite(bg, text_layer)
        bg.save('./img/banner.png')

    def generate_wishes(self, results):
        bg = Image.open('./img/wishes_bg.png').convert('RGBA')
        portraits = []
        xp = 0
        xp_book = Image.open(f'./img/xp_book.png')
        char = 0
        for item in results:
            if item == 'xp_book':
                xp += 1
            else:
                portraits.append(Image.open(f'./img/char_portrait/Character_{item}_Portrait.png').resize((390, 650)))
                char += 1
        tint_color = (255, 255, 255)  # White
        opacity = int(255 * .40)
        overlay = Image.new('RGBA', bg.size, tint_color + (0,))
        draw = ImageDraw.Draw(overlay)
        for i in range(char):
            draw.rectangle(((96 + i * 360, 265), (96 + (i + 1) * 360 - 12, 265 + 600)), outline=(255, 255, 255))
            draw.rectangle(((96 + i * 360, 265), (96 + (i + 1) * 360 - 12, 265 + 600)), fill=tint_color+(opacity,))

        bg = Image.alpha_composite(bg, overlay)
        for i in range(char):
            bg.paste(portraits[i], (81 + i * 360, 245), mask=portraits[i])
        bg.paste(xp_book, (96 + char * 360, 450), mask=xp_book)
        # text time
        text_layer = Image.new('RGBA', bg.size)
        txt = ImageDraw.Draw(text_layer)
        txt.text((600, 50), "Summon Results", (255, 209, 248), font=self.title_font)
        txt.text((595, 45), "Summon Results", (255, 255, 255), font=self.title_font)
        txt.text((96 + char * 360, 500), 'XP books: ', (255, 255, 255), font=self.subtitle_font)
        txt.text((96 + char * 360, 600), str(xp), (255, 255, 255), font=self.body_font)
        bg = Image.alpha_composite(bg, text_layer)
        bg.save('./img/results.png')
        bg.show()


def setup(client):
    client.add_cog(Pillow(client))
