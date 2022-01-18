# External Libraries
import os
from dotenv import load_dotenv

import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = discord.Client()

tournament = None

class Tournament():
	def __init__(self, guildId, textId, voiceId):
		self.guildId = guildId
		self.textId = textId
		self.voiceId = voiceId

		self.lobby = []
		self.teams = {}
	
	def __str__(self):
		return f"Tournament with {len(self.lobby)} players in lobby and {len(self.teams)} teams:\n{self.teams}"

class Team():
	def __init__(self, name, leader, roleId, textId, voiceId):
		self.name = name
		self.leader = leader

		self.roleId = roleId
		textId = textId
		voiceId = voiceId

		self.players = []
	
	def __str__(self):
		return f"Team \"{self.name}\", {len(self.players)} players."
	
	def __repr__(self):
		return str(self) + "\n"

class Player():
	def __init__(self, id):
		id = id

@client.event
async def on_ready():
	print(f"{client.user} has connected to Discord!")
	servers = await client.fetch_guilds().flatten()
	ids = []
	send = f"Currently connected to {len(servers)} servers: \""
	for i in range(len(servers)):
		ids.append(servers[i].id)
		send += servers[i].name
		send += "#"
		send += str(servers[i].id)
		if i < len(servers) - 2:
			send += "\", \""
		elif i == len(servers) - 2:
			send += "\" and \""
		else:
			send += "\"."
	print(send)

@client.event
async def on_message(message):
	if not message.author.bot:
		if "tournament bot" in message.content.lower():
			await message.reply("Hello World!")

# Tries to find the guild a slash command originated from, and returns feedback if unable to.
def findGuild(guildId, action = "do this"):
	if guildId is None:
		return f"Sorry, can't {action} in DMs."
	guild = None
	global client # TODO: Use context.me instead.
	for joinedGuild in client.guilds:
		if joinedGuild.id == guildId:
			guild = joinedGuild
			break
	if guild is None:
		return f"You need to invite Tournament Bot to {action}.\nInvite link: https://discord.com/api/oauth2/authorize?client_id=931495315834548244&permissions=285379664&scope=bot%20applications.commands"
	return guild

# Looks for the channel/category name in existingList, creates one if it's missing, and returns it. Filter function can be used as an additional filter.
async def findNameAsync(name, existingList, createFunctionAsync, filterFunction = None):
	for element in existingList:
		if element.name.lower() == name.lower() and (filterFunction is None or filterFunction(element)):
			return element
	return await createFunctionAsync(name)

# Looks for the many channel/category names in existingList, creates then if they're missing, and returns results in a list with the same order. Filter function can be used as an additional filter.
async def findOrCreateNamesAsync(names, existingList, createFunctionAsync, filterFunction = None):
	targets = dict.fromkeys(names) # Converts the list names to a dict with all values None.
	for element in existingList:
		anyNone = False
		for name in targets:
			if element.name.lower() == name.lower() and (filterFunction is None or filterFunction(element)):
				targets[name] = element
			if targets[name] is None:
				anyNone = True
		if not anyNone:
			break
	for name in targets:
		if targets[name] is None:
			targets[name] = await createFunctionAsync(name)
	return targets.values() # Only returns the created objects.

slash = SlashCommand(client, sync_commands = True)
guild_ids = [732240720487776356]

#@slash.subcommand(
#	base = "create",
#	name = "channels",
#	description = "Creates all necessary text and voice channels for the bot to function, if needed.",
#	guild_ids = guild_ids)
#async def createChannelsCommand(context):
#	guild = findGuild(context.guild_id, "create a tournament")
#	if not isinstance(guild, discord.Guild):
#		await context.send(guild)
#		return
#	await createChannels(guild)
#	await context.send(f"Created all necessary channels, use `/join` to start teams.")

@slash.subcommand(
	base = "tournament",
	name = "create",
	guild_ids = guild_ids
)
async def createTournamentCommand(context):
	guild = findGuild(context.guild_id, "create a tournament")
	if not isinstance(guild, discord.Guild):
		await context.send(guild)
		return
	global tournament
	if not tournament is None:
		await context.send("A tournament is already in progress, use `/tournament delete` to stop it.")
		return
	
	category = await findNameAsync("tournament", guild.categories, guild.create_category)
	infoText, generalText = await findOrCreateNamesAsync(["info", "general"], category.text_channels, category.create_text_channel)
	generalVoice = await findNameAsync("general", category.voice_channels, category.create_voice_channel)

	tournament = Tournament(guild.id, infoText.id, generalVoice.id)
	await context.send("Successfully created a tournament.")


@slash.subcommand(
	base = "tournament",
	name = "delete",
	guild_ids = guild_ids
)
async def deleteTournamentCommand(context):
	global tournament
	if tournament is None:
		await context.send("No tournament currently exists.")
		return
	guild = findGuild(context.guild_id, "delete a tournament")
	if not isinstance(guild, discord.Guild):
		await context.send(guild)
		return
	if tournament.guildId != guild.id:
		await context.send("The ongoing tournament is currently in another server. Multiple tournaments are currently not supported, sorry.")
		return
	tournament = None
	await context.send("Successfully deleted tournament.")

@slash.subcommand(
	base = "tournament",
	name = "show",
	guild_ids = guild_ids
)
async def tournamentDetailsCommand(context):
	global tournament
	if tournament is None:
		await context.send("No tournament currently exists, use `/tournament create` to make one.")
		return
	await context.send(str(tournament))

@slash.slash(
	name = "join",
	guild_ids = guild_ids
)
async def joinCommand(context):
	global tournament
	if tournament is None:
		await context.send("No tournament currently exists.")
		return
	guild = findGuild(context.guild_id, "join a tournament")
	if not isinstance(guild, discord.Guild):
		await context.send(guild)
		return
	if tournament.guildId != guild.id:
		await context.send("The ongoing tournament is currently in another server. Multiple tournaments are currently not supported, sorry.")
		return
	tournament.lobby.append(Player(context.author.id))
	await context.send(f"Successfully added {context.author.mention} to the lobby.")

try:
	client.run(TOKEN)
except discord.errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")