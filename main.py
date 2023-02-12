import asyncio
import json
import math
import random
import DiscordUtils
import aiofiles
import aiosqlite 
import discord
import requests
from DiscordUtils import NotConnectedToVoice
from discord.ext import commands
from discord.utils import get

with open("BadWords.txt", "r") as f:
    global badwords
    words = f.read()
    badwords = words.splitlines()

token_shush = "ODg0NDk0MzgzNTc0MDQ4Nzk4.YTZTlg.HBNPMNA_FSa12Z_aJFR6GscJui8"

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=";",
                      intents=discord.Intents.all(),
                      help_command=None,
                      case_insensitive=True)
client.multiplier = 5
client.warnings = {}
client.ticket_configs = {}
client.reaction_roles = []
music = DiscordUtils.Music()


def inspire_quote_get():
    reply = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(reply.text)
    inspirational_quote = json_data[0]["q"] + " - " + json_data[0]["a"]
    return inspirational_quote


async def initialize():
    await client.wait_until_ready()
    client.db = await aiosqlite.connect("SuitBotData.db")
    await client.db.execute(
        "CREATE TABLE IF NOT EXISTS SuitBotData (guild_id int, join_role int, join_channel int, join_message str, leave_message str, user_id int, exp int, identifier str, join_role_toggled bool, join_message_toggled bool, leave_message_toggled bool, feedback str, bot_channel str, music_channel str, logs_channel str, PRIMARY KEY (guild_id, user_id, identifier))"
    )


@client.event
async def on_guild_join(guild):
    await guild.create_role(name="Warning I",
                            colour=discord.Colour(0x95a5a6),
                            reason="Moderation by SuitBot")
    await guild.create_role(name="Warning II",
                            colour=discord.Colour(0x95a5a6),
                            reason="Moderation by SuitBot")
    await guild.create_role(name="Warning III",
                            colour=discord.Colour(0x95a5a6),
                            reason="Moderation by SuitBot")
    await guild.create_role(name="Warning I - After Kick",
                            colour=discord.Colour(0x546e7a),
                            reason="Moderation by SuitBot")
    await guild.create_role(name="Warning II - After Kick",
                            colour=discord.Colour(0x546e7a),
                            reason="Moderation by SuitBot")
    await guild.create_role(name="Warning III - After Kick",
                            colour=discord.Colour(0x546e7a),
                            reason="Moderation by SuitBot")


@client.event
async def on_raw_reaction_remove(payload):
    for role_id, msg_id, emoji in client.reaction_roles:
        if msg_id == payload.message_id and emoji == str(
                payload.emoji.name.encode("utf-8")):
            guild = client.get_guild(payload.guild_id)
            await guild.get_member(payload.user_id
                                   ).remove_roles(guild.get_role(role_id))
            return


@client.event
async def on_raw_reaction_add(payload):
    global category
    for role_id, msg_id, emoji in client.reaction_roles:
        if msg_id == payload.message_id and emoji == str(
                payload.emoji.name.encode("utf-8")):
            await payload.member.add_roles(
                client.get_guild(payload.guild_id).get_role(role_id))
            return
    if payload.member.id != client.user.id and str(
            payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = client.ticket_configs[
            payload.guild_id]

        if payload.message_id == msg_id:
            guild = client.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_channel = await category.create_text_channel(
                f"ticket-{payload.member.display_name}",
                topic=f"A ticket for {payload.member.display_name}.",
                permission_synced=True)

            await ticket_channel.set_permissions(payload.member,
                                                 read_messages=True,
                                                 send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            await ticket_channel.send(
                f"{payload.member.mention} Thank you for creating a ticket! Use **';close'** to close your ticket."
            )

            try:
                await client.wait_for("message",
                                      check=lambda m: m.channel ==
                                      ticket_channel and m.content == ";close",
                                      timeout=3600)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()


@client.command()
async def close(ctx):
    pass


@client.command()
@commands.has_permissions(administrator=True)
async def say(ctx):
    index = ctx.message.content.index(" ")
    string = ctx.message.content
    copy_msg = string[index:]
    await ctx.message.delete()
    await ctx.channel.send(copy_msg)


@client.command()
@commands.has_permissions(administrator=True)
async def set_reaction(ctx,
                       role: discord.Role = None,
                       msg: discord.Message = None,
                       emoji=None):
    if role != None and msg != None and emoji is not None:
        await msg.add_reaction(emoji)
        client.reaction_roles.append(
            (role.id, msg.id, str(emoji.encode("utf-8"))))

        async with aiofiles.open("reaction_roles.txt", mode="a") as file:
            emoji_utf = emoji.encode("utf-8")
            await file.write(f"{role.id} {msg.id} {emoji_utf}\n")

        await ctx.channel.send("Reaction has been set.")

    else:
        await ctx.send("Invalid arguments.")

@client.command()
@commands.has_permissions(administrator=True)
async def configure_ticket(ctx,
                           msg: discord.Message = None,
                           category: discord.CategoryChannel = None):
    if msg is None or category is None:
        await ctx.channel.send(
            "Failed to configure the ticket as an argument was not given or was invalid, please include the message id and then the category id."
        )
        return

    client.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id]

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(
            f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)

    await msg.add_reaction(u"\U0001F3AB")
    await ctx.channel.send("Successfully configured the ticket system.")


@client.event
async def on_ready():
    async with aiofiles.open("reaction_roles.txt", mode="a") as temp:
        pass

    async with aiofiles.open("reaction_roles.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            client.reaction_roles.append(
                (int(data[0]), int(data[1]), data[2].strip("\n")))
    for guild in client.guilds:
        client.warnings[guild.id] = {}

        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    client.warnings[guild.id][member_id][0] += 1
                    client.warnings[guild.id][member_id][1].append(
                        (admin_id, reason))

                except KeyError:
                    client.warnings[guild.id][member_id] = [
                        1, [(admin_id, reason)]
                    ]
    async with aiofiles.open("ticket_configs.txt", mode="a") as temp:
        pass

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            client.ticket_configs[int(
                data[0])] = [int(data[1]),
                             int(data[2]),
                             int(data[3])]
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="everything... | ;help"))
    print("We have logged in as {0.user}".format(client))


@client.command(aliases=["clr"])
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=3):
    await ctx.channel.purge(limit=amount + 1)


@client.command()
@commands.has_permissions(administrator=True)
async def purge(ctx):
    userMessages = []
    channel = client.get_channel(ctx.channel.id)
    async for message in channel.history():
        userMessages.append(message.content)
    await ctx.channel.purge(limit=len(userMessages))


@client.command()
async def inspire(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                if data[i] == ctx.channel.id:
                    correct_channel = True
        else:
            correct_channel = True
    if correct_channel:
        await ctx.channel.send(inspire_quote_get())


@client.command(aliases=["hi", "gday", "howdy"])
async def hello(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        await ctx.channel.send("Good Day to You!")


@client.command()
async def help(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        embed = discord.Embed(
            title="SuitBot Help Guide",
            description=
            ";help_simple - Simple Commands Help \n ;help_exp - Exp Help \n ;help_music - Music Help \n ;help_admin - Admin Help \n ;help_setup - Setup Help ",
            colour=discord.Colour.blue())
        embed.set_footer(text="Painfully made by SuitSnap")
        embed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        embed.set_author(
            name="SuitBot",
            icon_url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        await ctx.channel.send(embed=embed)


@client.command()
async def help_simple(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        embed = discord.Embed(
            title="SuitBot Simple Command Guide",
            description=
            ";ping - Tests the bot's ping \n ;inspire - A bit of hope in the world \n ;hello - Says hello!",
            colour=discord.Colour.blue())
        embed.set_footer(text="Painfully made by SuitSnap")
        embed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        embed.set_author(
            name="SuitBot",
            icon_url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        await ctx.channel.send(embed=embed)


@client.command()
async def help_exp(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        embed = discord.Embed(
            title="SuitBot Experience Command Guide",
            description=
            ";stats - Displays a user's exp stats \n ;leaderboard/lb - Shows the leaderboard for the server",
            colour=discord.Colour.blue())
        embed.set_footer(text="Painfully made by SuitSnap")
        embed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        embed.set_author(
            name="SuitBot",
            icon_url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        await ctx.channel.send(embed=embed)


@client.command()
async def help_music(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        embed = discord.Embed(
            title="SuitBot Help Command Guide",
            description=
            " ;join - Makes the bot join the voice channel the user is in \n ;leave - Makes the bot leave the voice channel \n ;play - Plays a song, or if a song is playing queues it \n ;pause - Pauses the song playing \n ;resume - Resumes the paused playing \n ;stop - Polls whether or not to stop playing music and empties the queue\n ;loop - Loops the currently playing song \n ;queue - Displays the queue for the server \n ;playing - Displays the song that is currently playing \n ;skip - Polls whether or not to skip the current song \n ;volume - Sets the volume of the music player 0-100 \n ;shuffle - Shuffles the queue \n",
            colour=discord.Colour.blue())
        embed.set_footer(text="Painfully made by SuitSnap")
        embed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        embed.set_author(
            name="SuitBot",
            icon_url=
            "https://cdn.discordapp.com/attachments/858433472962756638/882039343160631316/c.jpg"
        )
        await ctx.channel.send(embed=embed)


@client.command()
@commands.has_permissions(administrator=True)
async def help_admin(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        pass


@client.command()
@commands.has_permissions(administrator=True)
async def help_setup(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        pass


@client.event
async def on_member_join(member):
    try:
        toggle_msg = await client.db.execute(
            "SELECT join_message_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (member.guild.id, "Toggle"))
        toggle_msg = await toggle_msg.fetchone()
        toggle_msg = list(toggle_msg)
        toggled_msg = "".join(str(e) for e in toggle_msg)
        if toggled_msg != "0":
            async with client.db.execute(
                    "SELECT join_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                (member.guild.id, "Join Channel")) as channel:
                join_channel = await channel.fetchone()
                join_channel = join_channel[0]
                join_channel = client.get_channel(join_channel)
                async with client.db.execute(
                        "SELECT join_message FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                    (member.guild.id, "Join Message")) as cursor:
                    join_msg = await cursor.fetchone()
                    join_msg = join_msg[0]
                    join_msg = join_msg.format(member.mention)
                    await join_channel.send(join_msg)
                    async with client.db.execute(
                            "SELECT join_role FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                        (member.guild.id, "Join Role")) as role:
                        join_role = await role.fetchone()
                        join_role = join_role[0]
                        if join_role is not None:
                            toggled_role = await client.db.execute(
                                "SELECT join_role_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                                (member.guild.id, "Toggle"))
                            toggled_role = await toggled_role.fetchone()
                            toggled_role = toggled_role[0]
                            if toggled_role is not None:
                                toggled_role = list(toggled_role)
                                toggled_role = "".join(
                                    str(e) for e in toggled_role)
                            if toggled_role is None or toggled_role == "1":
                                joining_role = get(member.guild.roles,
                                                   id=join_role)
                                await member.add_roles(joining_role)
    except TypeError:
        pass


@client.command()
@commands.has_permissions(administrator=True)
async def add_role(ctx,
                   member: discord.Member = None,
                   role: discord.Role = None):
    await member.add_roles(role)
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(f"Added {role} to {member}")


@add_role.error
async def add_role_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.channel.send("The format is the member then the role!",
                               delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(
            "Make sure you include both the member and the role",
            delete_after=10)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(
            '**:x: | You do not have permission to use this command!**',delete_after =10)


@client.command()
@commands.has_permissions(administrator=True)
async def remove_role(ctx,
                   member: discord.Member = None,
                   role: discord.Role = None):
    await member.remove_roles(role)
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(f"Removed {role} from {member}")


@remove_role.error
async def remove_role_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.channel.send("The format is the member then the role!",
                               delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(
            "Make sure you include both the member and the role",
            delete_after=10)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(
            '**:x: | You do not have permission to use this command!**')


@client.event
async def on_member_remove(member):
    if member != client.user:
        try:
            toggle = await client.db.execute(
                "SELECT leave_message_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                (member.guild.id, "Toggle"))
            toggle = await toggle.fetchone()
            toggle = list(toggle)
            toggle = "".join(str(e) for e in toggle)
            if toggle == "None" or toggle == "1":
                async with client.db.execute(
                        "SELECT join_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                    (member.guild.id, "Join Channel")) as channel:
                    leave_channel = await channel.fetchone()
                    leave_channel = leave_channel[0]
                    leave_channel = client.get_channel(leave_channel)
                async with client.db.execute(
                        "SELECT leave_message FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                    (member.guild.id, "Leave Message")) as cursor:
                    leave_msg = await cursor.fetchone()
                    leave_msg = leave_msg[0]
                    leave_msg = leave_msg.format(member.mention)
                    await leave_channel.send(leave_msg)
        except TypeError:
            pass


@client.command()
@commands.has_permissions(administrator=True)
async def feedback(ctx):
    index = ctx.message.content.index(" ")
    string = ctx.message.content
    feedback_msg = string[index:]
    await client.db.execute(
        "INSERT INTO SuitBotData (feedback, identifier) VALUES (?,?)",
        (feedback_msg, "Feedback"))


@client.command()
@commands.has_permissions(administrator=True)
async def set_join_message(ctx):
    index = ctx.message.content.index(" ")
    string = ctx.message.content
    join_msg = string[index:]
    needs_to_contain = "{}"
    join_check = list(join_msg)
    matched_list = [
        characters in join_check for characters in needs_to_contain
    ]
    if all(matched_list):
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Join Message"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
            (ctx.guild.id, "Join Message"))
        await client.db.execute(
            "UPDATE SuitBotData SET join_message = ? WHERE guild_id = ? AND identifier = ?",
            (join_msg, ctx.guild.id, "Join Message"))
        await client.db.execute(
            "UPDATE SuitBotData SET join_message = join_message WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Join Message"))
        async with client.db.execute(
                "SELECT join_message FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Join Message")) as cursor:
            data = await cursor.fetchone()
            await ctx.channel.send("Join message set to:" + data[0])
    else:
        await ctx.channel.send(
            "Message needs to contain {} which mentions the joining player!")


@client.command()
@commands.has_permissions(administrator=True)
async def set_leave_message(ctx):
    index = ctx.message.content.index(" ")
    string = ctx.message.content
    leave_msg = string[index:]
    needs_to_contain = "{}"
    leave_check = list(leave_msg)
    matched_list = [
        characters in leave_check for characters in needs_to_contain
    ]
    if all(matched_list):
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Leave Message"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
            (ctx.guild.id, "Leave Message"))
        await client.db.execute(
            "UPDATE SuitBotData SET leave_message = ? WHERE guild_id = ? AND identifier = ?",
            (leave_msg, ctx.guild.id, "Leave Message"))
        await client.db.execute(
            "UPDATE SuitBotData SET leave_message = leave_message WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Leave Message"))
        async with client.db.execute(
                "SELECT leave_message FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Leave Message")) as cursor:
            data = await cursor.fetchone()
            await ctx.channel.send("Leave message set to:" + data[0])
    else:
        await ctx.channel.send(
            "Message needs to contain {} which mentions the leaving player!")


@client.command()
@commands.has_permissions(administrator=True)
async def set_join_role(ctx):
    index = ctx.message.content.index(" ")
    string = ctx.message.content
    join_role_info = string[index:]
    join_role = join_role_info.replace(">", "")
    join_role = join_role.replace("<", "")
    join_role = join_role.replace("@", "")
    join_role = join_role.replace("&", "")
    join_role = join_role.replace(" ", "")
    await client.db.execute(
        "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Join Role"))
    await client.db.execute(
        "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
        (ctx.guild.id, "Join Role"))
    await client.db.execute(
        "UPDATE SuitBotData SET join_role = ? WHERE guild_id = ? AND identifier = ?",
        (join_role, ctx.guild.id, "Join Role"))
    await client.db.execute(
        "UPDATE SuitBotData SET join_role = join_role WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Join Role"))
    await ctx.channel.send("Join role set to: " + join_role_info)


@client.command()
@commands.has_permissions(administrator=True)
async def set_join_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        join_channel = string[index:]
        int(join_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        join_channel = string[index:]
        join_channel = join_channel.replace(">", "")
        join_channel = join_channel.replace("#", "")
    await client.db.execute(
        "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Join Channel"))
    await client.db.execute(
        "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
        (ctx.guild.id, "Join Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET join_channel = ? WHERE guild_id = ? AND identifier = ?",
        (join_channel, ctx.guild.id, "Join Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET join_channel = join_channel WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Join Channel"))
    async with client.db.execute(
            "SELECT join_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Join Channel")) as cursor:
        data = await cursor.fetchone()
        await ctx.channel.send("Join and Leave message channel set to: " +
                               str(data[0]))


@client.command()
@commands.has_permissions(administrator=True)
async def set_log_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        log_channel = string[index:]
        int(log_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        log_channel = string[index:]
        log_channel = log_channel.replace(">", "")
        log_channel = log_channel.replace("#", "")
    await client.db.execute(
        "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel"))
    await client.db.execute(
        "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
        (ctx.guild.id, "Logs Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET logs_channel = ? WHERE guild_id = ? AND identifier = ?",
        (log_channel, ctx.guild.id, "Logs Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET logs_channel = logs_channel WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel"))
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        data = await cursor.fetchone()
        await ctx.channel.send("SuitBot logs channel set to: " + str(data[0]))


@client.command()
@commands.has_permissions(administrator=True)
async def toggle_join_message(ctx):
    toggle = await client.db.execute(
        "SELECT join_message_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Toggle"))
    toggle = await toggle.fetchone()
    if toggle is not None:
        toggle = list(toggle)
        toggle = "".join(str(e) for e in toggle)
    if toggle is None or toggle == "1":
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, join_message_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", False))
        await ctx.channel.send("Join message toggle set to: False")
    else:
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, join_message_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", True))
        await ctx.channel.send("Join message toggle set to: True")


@client.command()
@commands.has_permissions(administrator=True)
async def toggle_leave_message(ctx):
    toggle = await client.db.execute(
        "SELECT leave_message_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Toggle"))
    toggle = await toggle.fetchone()
    if toggle is not None:
        toggle = list(toggle)
        toggle = "".join(str(e) for e in toggle)
    if toggle is None or toggle == "1":
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, leave_message_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", False))
        await ctx.channel.send("Leave message toggle set to: False")
    else:
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, leave_message_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", True))
        await ctx.channel.send("Leave message toggle set to: True")


@client.command()
@commands.has_permissions(administrator=True)
async def toggle_join_role(ctx):
    toggle = await client.db.execute(
        "SELECT join_role_toggled FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Toggle"))
    toggle = await toggle.fetchone()
    if toggle is not None:
        toggle = list(toggle)
        toggle = "".join(str(e) for e in toggle)
    if toggle is None or toggle == "1":
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, join_role_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", False))
        await ctx.channel.send("Join role toggle set to: False")
    else:
        await client.db.execute(
            "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Toggle"))
        await client.db.execute(
            "INSERT INTO SuitBotData (guild_id, identifier, join_role_toggled) VALUES (?,?,?)",
            (ctx.guild.id, "Toggle", True))
        await ctx.channel.send("Join role toggle set to: True")


@client.command()
@commands.has_permissions(administrator=True)
async def add_bot_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        bot_channel = string[index:]
        int(bot_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        bot_channel = string[index:]
        bot_channel = bot_channel.replace(">", "")
        bot_channel = bot_channel.replace("#", "")
    await client.db.execute(
        "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
        (ctx.guild.id, "Bot Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET bot_channel = ? WHERE guild_id = ? AND identifier = ?",
        (bot_channel, ctx.guild.id, "Bot Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET bot_channel = bot_channel WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Bot Channel"))
    async with client.db.execute(
            "SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Bot Channel")) as cursor:
        data = await cursor.fetchone()
        await ctx.channel.send("Added a bot channel: " + str(data[0]))


@client.command()
@commands.has_permissions(administrator=True)
async def remove_bot_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        bot_channel = string[index:]
        int(bot_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        bot_channel = string[index:]
        bot_channel = bot_channel.replace(">", "")
        bot_channel = bot_channel.replace("#", "")
    await client.db.execute(
        "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ? AND bot_channel = ?",
        (ctx.guild.id, "Bot Channel", bot_channel))
    await ctx.channel.send("Removed a bot channel: " + bot_channel)


@client.command()
@commands.has_permissions(administrator=True)
async def add_music_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        music_channel = string[index:]
        int(music_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        music_channel = string[index:]
        music_channel = music_channel.replace(">", "")
        music_channel = music_channel.replace("#", "")
    await client.db.execute(
        "INSERT INTO SuitBotData (guild_id, identifier) VALUES (?,?)",
        (ctx.guild.id, "Music Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET music_channel = ? WHERE guild_id = ? AND identifier = ?",
        (music_channel, ctx.guild.id, "Music Channel"))
    await client.db.execute(
        "UPDATE SuitBotData SET music_channel = music_channel WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Music Channel"))
    async with client.db.execute(
            "SELECT music_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Music Channel")) as cursor:
        data = await cursor.fetchone()
        await ctx.channel.send("Added a music channel: " + str(data[0]))


@client.command()
@commands.has_permissions(administrator=True)
async def remove_music_channel(ctx):
    try:
        index = ctx.message.content.index(" ")
        string = ctx.message.content
        music_channel = string[index:]
        int(music_channel)
    except:
        index = ctx.message.content.index("#")
        string = ctx.message.content
        music_channel = string[index:]
        music_channel = music_channel.replace(">", "")
        music_channel = music_channel.replace("#", "")
    await client.db.execute(
        "DELETE FROM SuitBotData WHERE guild_id = ? AND identifier = ? AND music_channel = ?",
        (ctx.guild.id, "Bot Channel", music_channel))
    await ctx.channel.send("Removed a music channel: " + music_channel)


@client.event
async def on_message_delete(message):
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (message.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            if message.author == client.user:
                return
            else:
                await logs.send(
                    f"Author: {message.author}| Deleted message: {message.content}"
                )


@client.command()
async def ping(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        await ctx.send(f'Pong! In {round(client.latency * 1000)}ms')


@client.event
async def on_message_edit(before, after):
    msg = after.content
    swear_response = f"Hey, {after.author.mention}! Don't use that word!"
    try:
        if any(word in msg for word in badwords):
            async with client.db.execute(
                    "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
                (before.guild.id, "Logs Channel")) as cursor:
                logs = await cursor.fetchone()
                if logs is not None:
                    logs = logs[0]
                    logs = client.get_channel(logs)
                    await logs.send(
                        f"Author: {before.author} | Before: {before.content} | After: {after.content}"
                    )
                    await after.delete()
                    await after.channel.send(swear_response, delete_after=3)
    except:
        pass


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg = message.content.lower()
    swear_response = "Hey, {}! Don't use that word!".format(
        message.author.mention)
    if msg == "^":
        await message.channel.send("yeah yeah what they said")
    if message.author != client.user:
        cursor = await client.db.execute(
            "INSERT OR IGNORE INTO SuitBotData (guild_id, user_id, exp, identifier) VALUES (?,?,?, ?)",
            (message.guild.id, message.author.id, 1, "Experience"))

        if cursor.rowcount == 0:
            await client.db.execute(
                "UPDATE SuitBotData SET exp = exp + 1 WHERE guild_id = ? AND user_id = ? AND identifier = ?",
                (message.guild.id, message.author.id, "Experience"))
            cur = await client.db.execute(
                "SELECT exp FROM SuitBotData WHERE guild_id = ? AND user_id = ? AND identifier = ?",
                (message.guild.id, message.author.id, "Experience"))
            data = await cur.fetchone()
            exp = data[0]
            lvl = math.sqrt(exp) / client.multiplier

            if lvl.is_integer():
                await message.channel.send(
                    f"{message.author.mention} well done! You're now level: {int(lvl)}."
                )

        await client.db.commit()
        for word in badwords:
            if word in msg:
                await message.delete()
                await message.channel.send(swear_response, delete_after=3)
        await client.process_commands(message)


@client.command(aliases=["rank", "level", "lvl"])
async def stats(ctx,
                member: discord.Member = None):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if member is None: member = ctx.author

        async with client.db.execute(
                "SELECT exp FROM SuitBotData WHERE guild_id = ? AND user_id = ? AND identifier = ?",
            (ctx.guild.id, member.id, "Experience")) as cursor:
            data = await cursor.fetchone()
            exp = data[0]

        async with client.db.execute(
                "SELECT exp FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
            (ctx.guild.id, "Experience")) as cursor:
            rank = 1
            async for value in cursor:
                if exp < value[0]:
                    rank += 1

        lvl = int(math.sqrt(exp) // client.multiplier)

        current_lvl_exp = (client.multiplier * lvl)**2
        next_lvl_exp = (client.multiplier * (lvl + 1))**2

        lvl_percentage = ((exp - current_lvl_exp) /
                          (next_lvl_exp - current_lvl_exp)) * 100

        embed = discord.Embed(title=f"Stats for {member.name}",
                              colour=discord.Colour.gold())
        embed.add_field(name="Level", value=str(lvl))
        embed.add_field(name="Exp", value=f"{exp}/{next_lvl_exp}")
        embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}")
        embed.add_field(name="Level Progress",
                        value=f"{round(lvl_percentage, 2)}%")

        await ctx.send(embed=embed)


@client.command(aliases=["lb"])
async def leaderboard(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        buttons = {}
        for i in range(1, 6):
            buttons[
                f"{i}\N{COMBINING ENCLOSING KEYCAP}"] = i  # only show first 5 pages

        previous_page = 0
        current = 1
        entries_per_page = 10

        embed = discord.Embed(title=f"Leaderboard Page {current}",
                              description="",
                              colour=discord.Colour.gold())
        msg = await ctx.send(embed=embed)

        for button in buttons:
            await msg.add_reaction(button)

        while True:
            if current != previous_page:
                embed.title = f"Leaderboard Page {current}"
                embed.description = ""

                async with client.db.execute(
                        f"SELECT user_id, exp FROM SuitBotData WHERE guild_id = ? ORDER BY exp DESC LIMIT ? OFFSET ? ",
                    (
                        ctx.guild.id,
                        entries_per_page,
                        entries_per_page * (current - 1),
                    )) as cursor:
                    index = entries_per_page * (current - 1)

                    async for entry in cursor:
                        index += 1
                        member_id, exp = entry
                        member = ctx.guild.get_member(member_id)
                        embed.description += f"{index}) {member.mention} : {exp}\n"

                    await msg.edit(embed=embed)

            try:
                reaction, user = await client.wait_for(
                    "reaction_add",
                    check=lambda reaction, user: user == ctx.author and
                    reaction.emoji in buttons,
                    timeout=60.0)

            except asyncio.TimeoutError:
                return await msg.clear_reactions()

            else:
                previous_page = current
                await msg.remove_reaction(reaction.emoji, ctx.author)
                current = buttons[reaction.emoji]



@client.command()
@commands.has_permissions(administrator=True)
async def kick(ctx,
               member: discord.Member = None,):
    await member.kick()
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(f"Kicked:{member.mention}")


@client.command()
@commands.has_permissions(administrator=True)
async def ban(ctx,
              member: discord.Member = None):
    await member.ban()
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(f"Banned {member.mention}")


@client.command()
@commands.has_permissions(administrator=True)
async def unban(ctx,
                member: discord.Member = None,):
    await member.unban()
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(f"Unbanned {member.mention}")


@client.command()
@commands.has_permissions(administrator=True)
async def warn(ctx,
               member: discord.Member = None,
               *, reason=None):
    if member is None:
        return await ctx.send(
            "The provided member could not be found or you forgot to provide one."
        )

    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        first_warning = False
        client.warnings[ctx.guild.id][member.id][0] += 1
        client.warnings[ctx.guild.id][member.id][1].append(
            (ctx.author.id, reason))

    except KeyError:
        first_warning = True
        client.warnings[ctx.guild.id][member.id] = [
            1, [(ctx.author.id, reason)]
        ]

    count = client.warnings[ctx.guild.id][member.id][0]
    if count == 1:
        role = discord.utils.get(member.guild.roles, name="Warning I")
        if role is not None:
            await member.add_roles(role)
    elif count == 2:
        role = discord.utils.get(member.guild.roles, name="Warning II")
        if role is not None:
            await member.add_roles(role)
    elif count == 3:
        role = discord.utils.get(member.guild.roles, name="Warning III")
        if role is not None:
            await member.add_roles(role)
    elif count == 5:
        role = discord.utils.get(member.guild.roles,
                                 name="Warning I - After Kick")
        if role is not None:
            await member.add_roles(role)
    elif count == 6:
        role = discord.utils.get(member.guild.roles,
                                 name="Warning II - After Kick")
        if role is not None:
            await member.add_roles(role)
    elif count == 7:
        role = discord.utils.get(member.guild.roles,
                                 name="Warning III - After Kick")
        if role is not None:
            await member.add_roles(role)
    if count == 4:
        await member.kick()
    if count == 8:
        await member.ban()
    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.channel.send(
        f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}."
    )
    async with client.db.execute(
            "SELECT logs_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?",
        (ctx.guild.id, "Logs Channel")) as cursor:
        logs = await cursor.fetchone()
        if logs is not None:
            logs = logs[0]
            logs = client.get_channel(logs)
            logs.send(
                f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}."
            )


@client.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx,
                   member: discord.Member = None):
    if member is None:
        return await ctx.send(
            "The provided member could not be found or you forgot to provide one."
        )

    embed = discord.Embed(title=f"Displaying Warnings for {member.name}",
                          description="",
                          colour=discord.Colour.red())
    try:
        i = 1
        for admin_id, reason in client.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError:  # no warnings
        await ctx.send("This user has no warnings.")


@client.command()
async def join(ctx):
    correct_channel = False
    correct_vc = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    async with client.db.execute(
            'SELECT music_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Music Channel')) as voice_channel:
        extra = await voice_channel.fetchall()
        if len(extra) != 0:
            for i in range(len(extra)):
                channel = str(extra[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str((ctx.author.voice.channel.id)):
                    correct_vc = True
        else:
            correct_vc = True
    if correct_channel:
        if ctx.author.voice is None:
            return await ctx.send(
                "You are not connected to a voice channel, please connect to the music channel"
            )

        if ctx.voice_client is not None:
            ctx.send("Already connected!")

        if ctx.author.voice is not None and correct_vc:
            return await ctx.author.voice.channel.connect()


@client.command()
async def leave(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()
        await ctx.send("I am not connected to a voice channel currently")


@client.command()
async def play(ctx,
               *, url):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            if not player:
                player = music.create_player(ctx, ffmpeg_error_betterfix=True)
            if not ctx.voice_client.is_playing():
                await player.queue(url, search=True)
                song = await player.play()
                await ctx.send(f"Playing {song.name}")
            else:
                song = await player.queue(url, search=True)
                await ctx.send(f"Queued {song.name}")
            return
        await ctx.channel.send("I am not currently connected to a voice channel")

@client.command()
async def pause(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            song = await player.pause()
            await ctx.send(f"Paused {song.name}")
            return
        await ctx.channel.send("I am not currently connected to a voice channel")


@client.command()
async def resume(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            song = await player.resume()
            await ctx.send(f"Resumed {song.name}")
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")



@client.command()
async def stop(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            poll = discord.Embed(
                title=
                f"Vote to Stop Music by - {ctx.author.name}#{ctx.author.discriminator}",
                description=
                "**80% of the voice channel must vote to stop for it to pass.**",
                colour=discord.Colour.blue())
            poll.add_field(name="Stop", value=":white_check_mark:")
            poll.add_field(name="Keep Playing", value=":no_entry_sign:")
            poll.set_footer(text="Voting ends in 15 seconds.")

            poll_msg = await ctx.send(embed=poll)
            poll_id = poll_msg.id
            await poll_msg.add_reaction(u"\u2705")  # yes
            await poll_msg.add_reaction(u"\U0001F6AB")  # no

            await asyncio.sleep(15)

            poll_msg = await ctx.channel.fetch_message(poll_id)

            votes = {u"\u2705": 0, u"\U0001F6AB": 0}
            reacted = []
            for reaction in poll_msg.reactions:
                if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                    async for user in reaction.users():
                        try:
                            if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                                votes[reaction.emoji] += 1

                                reacted.append(user.id)
                        except:
                            pass
            stop = False

            if votes[u"\u2705"] > 0:
                if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                        votes[u"\u2705"] +
                        votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                    stop = True
                    embed = discord.Embed(
                        title="Stop Successful",
                        description=
                        "***Voting to stop playing was successful, stopping now.***",
                        colour=discord.Colour.green())

            if not stop:
                embed = discord.Embed(
                    title="Stop Failed",
                    description=
                    "*Voting to stop playing has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to stop.**",
                    colour=discord.Colour.red())

            embed.set_footer(text="Voting has ended.")

            await poll_msg.clear_reactions()
            await poll_msg.edit(embed=embed)

            if stop:
                player = music.get_player(guild_id=ctx.guild.id)
                await player.stop()
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")

        '''player = music.get_player(guild_id=ctx.guild.id)
        await player.stop()
        await ctx.send("Stopped")'''


@client.command()
async def loop(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            song = await player.toggle_song_loop()
            if song.is_looping:
                await ctx.send(f"Enabled loop for {song.name}")
            else:
                await ctx.send(f"Disabled loop for {song.name}")
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")


@client.command()
async def queue(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:
        if ctx.voice_client is not None:
            try:
                player = music.get_player(guild_id=ctx.guild.id)
                embed = discord.Embed(title="Song Queue",
                                      description="",
                                      colour=discord.Colour.dark_gold())
                if len(player.current_queue()) > 0:
                    for i in range(len(player.current_queue())):
                        if i == 0:
                            embed.description += f"Now playing: {[song.name for song in player.current_queue()][0]}\n"
                        else:
                            embed.description += f"{i}: {[song.name for song in player.current_queue()][i]}\n"
                            i += 1
                    embed.set_footer(text="Painfully made by SuitSnap")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Song Queue",
                                          description="",
                                          colour=discord.Colour.dark_gold())
                    embed.description += "Song Queue is empty currently, use ;play to add songs!"
                    embed.set_footer(text="Painfully made by SuitSnap")
                    await ctx.send(embed=embed)
            except AttributeError:
                embed = discord.Embed(title="Song Queue",
                                      description="",
                                      colour=discord.Colour.dark_gold())
                embed.description += "Song Queue is empty currently, use ;play to add songs!"
                embed.set_footer(text="Painfully made by SuitSnap")
                await ctx.send(embed=embed)
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")


@client.command(aliases=["now_playing", "playing"])
async def np(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            try:
                player = music.get_player(guild_id=ctx.guild.id)
                song = player.now_playing()
                await ctx.send(f"Now playing: {song.name}")
            except AttributeError:
                await ctx.send("No songs playing currently")
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")


@client.command()
async def skip(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            poll = discord.Embed(
                title=
                f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                description=
                "**80% of the voice channel must vote to skip for it to pass.**",
                colour=discord.Colour.blue())
            poll.add_field(name="Skip", value=":white_check_mark:")
            poll.add_field(name="Stay", value=":no_entry_sign:")
            poll.set_footer(text="Voting ends in 15 seconds.")

            poll_msg = await ctx.send(embed=poll)
            poll_id = poll_msg.id
            await poll_msg.add_reaction(u"\u2705")  # yes
            await poll_msg.add_reaction(u"\U0001F6AB")  # no

            await asyncio.sleep(15)

            poll_msg = await ctx.channel.fetch_message(poll_id)

            votes = {u"\u2705": 0, u"\U0001F6AB": 0}
            reacted = []
            for reaction in poll_msg.reactions:
                if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                    async for user in reaction.users():
                        try:
                            if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                                votes[reaction.emoji] += 1

                                reacted.append(user.id)
                        except:
                            pass

            skip = False

            if votes[u"\u2705"] > 0:
                if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                        votes[u"\u2705"] +
                        votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                    skip = True
                    embed = discord.Embed(
                        title="Skip Successful",
                        description=
                        "***Voting to skip the current song was successful, skipping now.***",
                        colour=discord.Colour.green())

            if not skip:
                embed = discord.Embed(
                    title="Skip Failed",
                    description=
                    "*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**",
                    colour=discord.Colour.red())

            embed.set_footer(text="Voting has ended.")

            await poll_msg.clear_reactions()
            await poll_msg.edit(embed=embed)

            if skip:
                player = music.get_player(guild_id=ctx.guild.id)
                data = await player.skip(force=True)
                await ctx.send(f"Skipped {data[0].name}")
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")


@client.command()
async def volume(ctx, vol):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            song, volume = await player.change_volume(
                float(vol) / 100)  # volume should be a float between 0 to 1
            await ctx.send(f"Changed volume for {song.name} to {volume * 100}%")
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")



@client.command()
async def remove(ctx, index=None):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            if index is not None:
                song = await player.remove_from_queue(int(index))
                await ctx.send(f"Removed {song.name} from queue")
            else:
                await ctx.send("Please specify which song to remove from the queue"
                               )
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")

@client.command()
async def shuffle(ctx):
    correct_channel = False
    async with client.db.execute(
            'SELECT bot_channel FROM SuitBotData WHERE guild_id = ? AND identifier = ?',
        (ctx.guild.id, 'Bot Channel')) as cursor:
        data = await cursor.fetchall()
        if len(data) != 0:
            for i in range(len(data)):
                channel = str(data[i])
                channel = channel.replace("(", "")
                channel = channel.replace(")", "")
                channel = channel.replace(",", "")
                channel = channel.replace(" ", "")
                if channel == str(ctx.channel.id):
                    correct_channel = True

        else:
            correct_channel = True
    if correct_channel:

        if ctx.voice_client is not None:
            player = music.get_player(guild_id=ctx.guild.id)
            try:
                copy = [player.current_queue()][1:]
                random.shuffle(copy)
                player.current_queue()[1:] = copy
                embed = discord.Embed(title="Shuffle",
                                      description="Queue shuffled!",
                                      footer="Painfully made by SuitSnap")
                await ctx.send(embed=embed)
            except AttributeError:
                embed = discord.Embed(title="Shuffle",
                                      description="No songs to shuffle!",
                                      footer="Painfully made by SuitSnap")
                await ctx.send(embed=embed)
            return
        await ctx.channel.send("I am not currently connected to a voice channel!")


client.loop.create_task(initialize())
client.run(token_shush)
