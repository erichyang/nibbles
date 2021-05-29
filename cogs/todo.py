import discord
from discord.ext import commands
from tinydb import TinyDB, Query


def todo_embed(uid, author_name):
    with TinyDB('./data/todo.json') as db:
        todo = db.search(Query().user == uid)
        if len(todo) == 0:
            return None
        todo = todo[0].get('todo')
        desc = '\n'
        for index, task in enumerate(todo):
            desc += f'{index + 1}. {task}\n\n'
        title = f"{len(todo)} Tasks" if len(todo) > 0 else 'Congratulations, you finished your tasks!'
        embed = discord.Embed(title=title, colour=discord.Colour(0x24bdff), description=desc)

        embed.set_author(name=author_name)
        return embed


class Todo(commands.Cog):

    def __init__(self, client):
        self.client = client

    # events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Todo online')

    # commands
    @commands.command(description='add an item to your to-do list!\n.todo_add <item>; .add', aliases=['add'])
    async def todo_add(self, ctx, *, item):
        with TinyDB('./data/todo.json') as db:
            todo = db.search(Query().user == ctx.author.id)
            if len(todo) != 0:
                new_list = todo[0].get('todo')
                new_list.append(item)
                db.update({'user': ctx.author.id, 'todo': new_list}, Query().user == ctx.author.id)
            else:
                db.insert({'user': ctx.author.id, 'todo': [item]})
        async for message in ctx.channel.history(limit=10):
            if message.author.bot and 'to-do' in message.content:
                await message.delete()
        await ctx.send(content='Added to your todo list!', embed=todo_embed(ctx.author.id,
                                                                            ctx.author.display_name if ctx.author.nick is None else ctx.author.nick))

    @commands.command(description='view your to-do list!\n.todo_list; .list; .todo', aliases=['todo', 'list'])
    async def todo_list(self, ctx):
        if ctx.author.id in [513424144541417483, 201687181238992896] and len(ctx.message.mentions) != 0:
            user = ctx.message.mentions[0]
        else:
            user = ctx.author
        name = user.display_name if user.nick is None else user.nick
        embed = todo_embed(user.id, name)
        async for message in ctx.channel.history(limit=10):
            if message.author.bot and 'to-do' in message.content:
                await message.delete()
        if embed is not None:
            await ctx.send(content=f"{name}'s to-do list", embed=embed)
        else:
            await ctx.send(content=f"{name} does not have a to-do list yet!")

    @commands.command(description='check off a task from your to-do list\n.todo_check 3;.check 1', aliases=['check', 'remove'])
    async def todo_check(self, ctx, value):
        with TinyDB('./data/todo.json') as db:
            todo = db.search(Query().user == ctx.author.id)
            if len(todo) != 0:
                todo = todo[0].get('todo')
            else:
                await ctx.send('this user has not made a todo list yet')
                return
            new_list = todo
            if value.isdigit():
                value = int(value)
            if isinstance(value, str):
                new_list.remove(value)
            elif len(todo) >= value:
                new_list.pop(value - 1)
            else:
                await ctx.send('such task does not exist :(')
                return
            db.update({'user': ctx.author.id, 'todo': new_list}, Query().user == ctx.author.id)
            async for message in ctx.channel.history(limit=10):
                if message.author.bot and 'to-do' in message.content:
                    await message.delete()
            await ctx.send(content='todo task has been checked off!', embed=todo_embed(ctx.author.id, ctx.author.display_name if ctx.author.nick is None else ctx.author.nick))


def setup(client):
    client.add_cog(Todo(client))
