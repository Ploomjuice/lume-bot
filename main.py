import discord.errors
from discord import Intents, Message, Member, Embed, Color, app_commands
import os
from responses import get_response
from Levenshtein import ratio
from discord.ext import commands
import random
from db_apis import Quote_API
import asyncio
from collections import Counter, defaultdict
import re

# bot intents
intents: Intents = Intents.default()  # Start with default intents.
intents.message_content = True  # NOQA
intents.message_content = True  # NOQA
intents.guilds = True # NOQA
intents.members = True  # NOQA

# bot init
bot = commands.Bot(command_prefix=']', intents=intents)
user = os.environ['user']
password = os.environ['password']
quotes_db = Quote_API()

# flags
quiz_in_progress = False
in_progress = defaultdict(bool)


# FUNCTIONALITY
async def send_message(message: Message, user_message):
    # add more messages,

    if not user_message:
        print('(Message was empty because intents were not enabled (probably))')
        return
    # private message
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    try:
        if 'lume' in message.content.lower().split():
            pass
            # await message.channel.send('shut the fuck up')

        await bot.process_commands(message)

        # response: str = get_response(user_message)
        # await message.author.send(response) if is_private else await message.channel.send(response)

    # add logging later
    except Exception as e:
        print(e)

# STARTUP


# register an event
@bot.event
async def on_ready() -> None:

    await quotes_db.dbu.connect(user, password, 'quotes')
    print("hi motherfuckers and fothermuckers it's Lume")


# triggers when a message is received from someone else
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    elif message.content.startswith('$hello'):
        await message.channel.send('yoruamo')

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)

# COMMANDS
"""
Commands are organized by category, and then further by game-sections for games
"""


@bot.command()
async def ping(ctx):

    latency = round(bot.latency * 1000)  # latency in ms
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"Latency: {latency}ms",
        color=Color.blurple()
    )
    await ctx.send(embed=embed)

# Quote Game
"""
Quote Guessing Game
List of commands:
- ]add_quote : adds a quote to the respective quote database
- ]view_quotes: observes a section of all quotes added in a server
- ]  
"""


@bot.command()
async def commands(ctx):

    commands_list = Embed(
        title="List of Commands:",
        description="""
        **]ping**: Pong!\n
        **]commands**: View List of commands\n
        **]quotes_list** *<page_no>*: View all quotes in this server\n
        **]add_quote** *<@mention> <content>*: Adds a quote to the server database\n
        **]delete_quote** *<quote_id>*: Deletes a quote from the server database, use with caution!\n
        **]quotes_quiz** *<length>*: Starts a "guess who said it?" quiz with the stored quotes\n
        
        """,
        color=Color.purple()
    ).set_footer(text="More commands coming soon!").set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=commands_list)


@bot.command()
async def add_quote(ctx, mention: Member, *, content: str):
    """
    Things to add:
    - Make Pings Mandatory (resolved)
    - Check against duplicates (resolved)
    - ping for confirmation (resolved)

    :param ctx: context
    :param mention: Utterer username
    :param content: message/quote to be added
    :return: nothing
    """
    channel = ctx.channel
    server = str(ctx.guild).replace("'", "")
    await quotes_db.refresh_ids(server)

    author = ctx.author

    if len(content) > 195:
        await ctx.send("Your quote is too long! Quotes must be at most 195 characters long!")
        return

    response = Embed(
        title=f"**Quote added by {author.name}: **",
        description=f'"{content}" - {mention.mention}',
        color=Color.blurple()


    ).set_footer(text=f"{server}: #{channel}")

    # check for dupes
    quote_df = await quotes_db.load_db(server)
    contents = quote_df["content"]
    await ctx.send("Checking Quote...")

    # look for too-similar quotes
    problem_quotes = []
    for idx, quote in enumerate(contents):
        sim_score = ratio(content, quote)

        if sim_score >= 0.7:
            username, _ = await quotes_db.retrieve_quote(server, idx+1)
            problem_quotes.append((username, quote))

    # deliver warning
    if len(problem_quotes) != 0:
        desc = "The quote you are trying to add is very similar at least one other quote in the database:"
        for username, quote in problem_quotes:
            desc += f'\n - "{quote}" - **{username}**'
        desc += "\nIf you still wish to proceed, respond with y/yes, otherwise, respond with n/no"
        warning = Embed(
            title="Warning!",
            description=desc,
            color=Color.dark_red()
        )

        await ctx.send(embed=warning)
        try:
            def confirm(m):
                return (m.author.id == ctx.author.id and m.channel.id == channel.id and m.content.lower() in
                        ["y", "yes", "n", "no"])

            message = await bot.wait_for("message", timeout=60.0, check=confirm)
            if message.content.lower() in ["y", "yes"]:
                await ctx.send(f"Proceeding...")
                pass
            elif message.content.lower() in ['n', "no"]:
                await ctx.send("Process cancelled.")
                return
        except TimeoutError:
            await ctx.send("Timed out. Action cancelled.")

    # normal progression
    if author.id == mention.id:
        # directly act
        await quotes_db.add_quote(int(mention.id), str(mention.name), str(content), str(channel), str(server),
                                  str(author))
        await ctx.send(embed=response)
    else:

        await ctx.send(f"{mention.mention}, do you give consent to the following quote being added?\n"
                       f'"{content}" - {mention.mention}\n'
                       "-# Respond with y/yes to proceed, or n/no to reject.")
        try:
            def check(m):
                return (m.author.id == mention.id and m.channel.id == channel.id and m.content.lower() in
                        ["y", "yes", "n", "no"])
            # Wait for a message mentioning the specified user

            message = await bot.wait_for("message", timeout=120.0, check=check)
            if message.content.lower() in ["y", "yes"]:
                await ctx.send(f"Quote permitted.  Adding quote to database...")
                await quotes_db.add_quote(int(mention.id), str(mention.name), str(content), str(channel), str(server),
                                          str(author))
                await quotes_db.refresh_ids(server)
                await ctx.send(embed=response)
            elif message.content.lower() in ['n', "no"]:
                await ctx.send("Quote has been rejected. Action Cancelled.")
        except TimeoutError:
            await ctx.send("Timed out. Action cancelled.")


@bot.command()
async def delete_quote(ctx, quote_id):

    server = str(ctx.guild).replace("'", "")
    await quotes_db.refresh_ids(server)

    # find quote
    username, content = await quotes_db.retrieve_quote(server, quote_id)

    # Ask for confirmation
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["y", "yes", "n", "no"]
    try:
        ask = Embed(
            title="Are you sure you wish to delete the following quote?",
            description=f'"{content}" - **{username}**',
            color=Color.dark_red()
        ).add_field(name="Warning!", value="This action cannot be reversed!").set_footer(text="Type y/yes to proceed,"
                                                                                              "n/no to cancel.")
        await ctx.send(embed=ask)
        # Wait for the user's response
        response = await bot.wait_for("message", timeout=60.0, check=check)
        if response.content.lower() in ["y", "yes"]:
            await ctx.send("Confirmed.  Deleting Quote...")
            # delete the quote
            await quotes_db.delete_quote(quote_id, f"{server}")
            await quotes_db.refresh_ids(server)
        else:
            await ctx.send("Action cancelled.")
            return

    except asyncio.TimeoutError:
        await ctx.send("No response received. Action cancelled.")
        return

    except IndexError:
        await ctx.send(f"Quote with ID: {quote_id} does not exist.  Action cancelled.")
        return

    response = (f"Quote Deleted.  \n"
                f"-# quote_id: {quote_id}")
    await ctx.send(response)


@bot.command()
async def quotes_list(ctx, page=1):
    server = str(ctx.guild).replace("'", "")
    if in_progress[server]:
        await ctx.send("This command cannot be used while a quiz is in progress!")
        return

    start = 10 * (page - 1)
    end = 10 * page
    server_quotes = await quotes_db.load_db(server)
    if len(server_quotes) < 10:
        end = len(server_quotes)
    display = server_quotes[start:end]
    response = [f"**Quotes in {server}** - Page {page}: \n"]

    # filter pings
    pattern = r"<@!?(\d+)>"
    i = 1 + start
    for _, name, message in list(display.itertuples(index=False, name=None)):
        # find pings to filter
        for ping_ in re.findall(pattern, message):
            discord_user = ctx.guild.get_member(int(ping_)) or await ctx.guild.fetch_member(int(ping_))

            # lookup and replace pings
            if discord_user:

                display_name = discord_user.nick if discord_user.nick else discord_user.name

                message = message.replace(f"<@{ping_}>", f"@{display_name}")
        # create list
        list_item = f'**{i}.** "{message}" - **{name}**\n'
        response += list_item

        i += 1
    quote_embed = Embed(
        title=response.pop(0),
        description=''.join(response)
    )
    await ctx.send(embed=quote_embed)


@bot.command()
async def quotes_quiz(ctx, length):

    server = str(ctx.guild).replace("'", "")
    if in_progress[server]:
        await ctx.send("A quiz is already in progress!")
        return
    else:
        in_progress[server] = True
    scoreboard = Counter()
    player_uids = {}

    try:
        length = int(length)

    except:
        in_progress[server] = False
        await ctx.send(f"Please enter a proper number! (improper value: \"{length}\")")
        return

    # load quotes
    server_quotes = await quotes_db.load_db(server)
    maximum, _ = server_quotes.shape
    quotes = list(server_quotes['content'])
    answers = list(server_quotes['username'])
    uids = list(server_quotes['discord_uid'])

    # check for size constraint
    if length > maximum:
        await ctx.send(f"**This server does not have enough quotes to start a quiz of size {length}!**\n"
                       f"-# This server only has {maximum} quotes.")
        in_progress[server] = False
        return
    else:
        # start quiz
        await ctx.send("**QUOTE QUIZ STARTING IN 5 SECONDS...**")
        await asyncio.sleep(5)

    def check(guess):
        return sender == guess.content and guess.channel == ctx.channel

    # select quotes
    for i in range(length):
        random_id = random.randint(1, maximum)
        sender = answers.pop(random_id-1)
        random_quote = quotes.pop(random_id-1)

        # aesthetic
        id = uids.pop(random_id-1)

        maximum -= 1

        # ask question

        question = Embed(
            title="Who sent the following message?",
            description=f"{random_quote}",
            color=Color.dark_purple()
        )
        question.set_footer(text="Please type the username, not the nickname or display name!")

        await ctx.send(embed=question)

        try:
            member = await ctx.guild.fetch_member(id)
            sender_pfp = member.display_avatar.url

            # Wait for a message mentioning the specified user
            message = await bot.wait_for("message", timeout=20.0, check=check)
            correct = Embed(
                title="Correct!",
                description=f"{message.author.mention} got it right first!\n The answer was **{sender}**!\n",
                color=Color.green()
            ).set_thumbnail(url=message.author.avatar.url)
            if member:
                correct.set_image(url=sender_pfp)
            else:
                correct.set_footer(text=f"I miss {sender}... :pensive:")

            await ctx.send(embed=correct)

            # update score
            scoreboard[message.author.name] += 1

            # check for players
            if message.author.id not in player_uids:
                player_uids[message.author.name] = message.author.id

            # buffer
            await asyncio.sleep(3)
            if i != length - 1:
                await ctx.send("**Next Question...**")
            await asyncio.sleep(3)

        except TimeoutError:
            reveal = Embed(
                title="Time's up!",
                description=f"Nobody got it right! The correct answer was {sender}!",
                color=Color.dark_red()
            ).set_image(url=sender_pfp)

            await ctx.send(embed=reveal)
            await asyncio.sleep(3)
            if i != length - 1:
                await ctx.send("**Next Question...**")
            await asyncio.sleep(3)

    # end game stats
    sorted_scoreboard = sorted(scoreboard.items(), key=lambda item: item[1], reverse=True)
    if len(sorted_scoreboard) == 0:
        in_progress[server] = False
        await ctx.send("lmao you guys suck")
        return
    high_score = sorted_scoreboard[0][1]
    players = await quotes_db.load_players(server)
    ranks = []

    # update leaderboard
    for idx, (player, score) in enumerate(sorted_scoreboard):
        previous_score = None

        # add player to players table if not existing
        if player not in players:

            # add to player table
            await quotes_db.add_player(player_uids[player], player, str(server))

        if score == high_score:
            await quotes_db.update_leaderboard(player_uids[player], correct=score, win=1)
            print(f"{player}'s score increased by {score}")
        else:
            await quotes_db.update_leaderboard(player_uids[player], correct=score, win=0)
            print(f"{player}'s score increased by {score}")

        # create leaderboard
        if score != previous_score:
            rank = idx + 1
            previous_score = score
            # build rankings
            if rank == 1:
                ranks.append(f"**{rank}. {player} - {score}**")
            else:
                ranks.append(f"{rank}. {player} - {score}")

    leaderboard = ('\n'.join(ranks))

    lb = Embed(
        title="Game Over!",
        description="Congratulations to the winners! Woohoo! Yippee!",
        color=Color.yellow()
    ).add_field(name="__Leaderboard__", value=leaderboard)

    in_progress[server] = False
    await ctx.send(embed=lb)


@bot.command()
async def frame_quote(ctx, quote):
    pass

# PROFILE COMMANDS


@bot.command()
async def set_nickname(ctx, nicknames):
    if len(nicknames) == 1:
        nicknames = [nicknames]
    pass


# MAIN ENTRY POINT
def main() -> None:
    bot.run(token=os.getenv('token'))


if __name__ == '__main__':
    main()
    