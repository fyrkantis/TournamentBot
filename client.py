# External Libraries
from random import choice
import os
from sqlite3 import connect
from dotenv import load_dotenv

from discord import Client, Color, PermissionOverwrite, errors
from discord.utils import get
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = Client()

tournaments = {}
colors = {
	"Cyan": Color.teal(),
	"Green": Color.green(),
	"Blue": Color.blue(),
	"Purple": Color.purple(),
	"Magenta": Color.magenta(),
	"Yellow": Color.gold(),
	"Orange": Color.orange(),
	"Red": Color.red()
}

# Main classes.

class Tournament():
	def __init__(self, guildId, leaderRoleId, categoryId, infoId, textId, voiceId):
		self.guildId = guildId
		self.leaderRoleId = leaderRoleId
		self.categoryId = categoryId
		self.infoId = infoId
		self.textId = textId
		self.voiceId = voiceId

		self.lobby = []
		self.teams = {}
	
	def __str__(self):
		return f"Tournament with {len(self.lobby)} players in lobby and {len(self.teams)} teams:\n{self.teams}"

class Team():
	def __init__(self, leaderId, roleId, textId, voiceId):
		self.leaderId = leaderId

		self.roleId = roleId
		textId = textId
		voiceId = voiceId

		self.players = []
	
	def __str__(self):
		return f"Team containing {len(self.players)} players."
	
	def __repr__(self):
		return str(self) + "\n"

class Player():
	def __init__(self, id):
		id = id

# Basic events.

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

# Lots of fancy help functions for slash commands.

# Just tries to find the guild a slash command originated from.
def findGuild(guildId, action = "do this"):
	if guildId is None:
		return None, f"Sorry, you can't {action} in DMs."
	guild = None
	global client # TODO: Use context.me instead.
	for joinedGuild in client.guilds:
		if joinedGuild.id == guildId:
			guild = joinedGuild
			break
	if guild is None:
		return None, f"You need to invite Tournament Bot to {action}.\nInvite link: https://discord.com/api/oauth2/authorize?client_id=931495315834548244&permissions=285379664&scope=bot%20applications.commands"
	return guild, None

# This is a common function in most commands to ensure that the current guild is valid and has an ongoing tournament.
def findGuildTournament(guildId, action = "do this", tournamentNone = False):
	guild, error = findGuild(guildId, action)
	if not error is None: # Passes error from findGuild.
		return None, error
	if not tournamentNone and guildId != guild.id:
		return None, f"You can't {action} because the ongoing tournament is in another server. Multiple tournaments are currently not supported, sorry."
	
	# Looks if specified tournament exists. tournamentNone decides if the tournament should exists; if it doesn't match the result, an error message is returned instead of None.
	if (tournaments.get(guildId) is None) != tournamentNone:
		if tournamentNone: # Decides if globalTournament should be None.
			return None, f"You can't {action} because a tournament already exists, use `/tournament delete` to stop it."
		else:
			return None, f"You can't {action} because no tournament currently exists, use `/tournament create` to start one."
	return guild, None # Returns the guild object, current global tournament variable (which should be by reference since objects are mutable), and a potential error message.

# Looks for the channel/category name in existingList, creates one if it's missing, and returns it.
# External input can be used to bypass if it already contains something. Filter function can be used as an additional filter.
async def findOrCreateNameAsync(name, existingList, createFunctionAsync, externalInput = None, filterFunction = None, **createArgs):
	if not externalInput is None: # TODO: Better parameter naming scheme.
		return externalInput
	for element in existingList:
		if element.name.lower() == name.lower() and (filterFunction is None or filterFunction(element)):
			return element
	return await createFunctionAsync(name = name, **createArgs)

# Looks for the many channel/category names in existingList, creates then if they're missing, and returns results in a list with the same order.
# Names can be a list, or a dictionary with default values. Filter function can be used as an additional filter.
async def findOrCreateNamesAsync(names, existingList, createFunctionAsync, filterFunction = None, **createArgs):
	if isinstance(names, list):
		names = dict.fromkeys(names) # Converts the list names to a dict with all values None.
	for name in names:
		if not names[name] is None:
			continue
		for element in existingList:
			if element.name.lower() == name.lower() and (filterFunction is None or filterFunction(element)):
				names[name] = element
				break
		if names[name] is None:
			names[name] = await createFunctionAsync(name, **createArgs)
	return names.values() # Only returns the created objects.

# Does the actual slash commands.

slash = SlashCommand(client, sync_commands = True)
guild_ids = [732240720487776356]

@slash.subcommand(
	base = "tournament",
	name = "create",
	description = "Create a tournament people can join and create teams in.",
	options = [{
			"name": "existing-leader-role",
			"description": "Use existing leader role instead of creating one. (doesn't have to be named \"Tournament Leader\")",
			"type": 8,
			"required": False
		}, {
			"name": "existing-category",
			"description": "Use existing category instead of creating one. (doesn't have to be named \"Tournament\")",
			"type": 7,
			"channel_types": [4],
			"required": False
		}, {
			"name": "existing-info-text",
			"description": "Use existing text channel for info instead of creating one. (doesn't have to be named \"info\")",
			"type": 7,
			"channel_types": [0],
			"required": False
		}, {
			"name": "existing-general-text",
			"description": "Use existing text channel instead of creating one. (that doesn't have to be named \"general\")",
			"type": 7,
			"channel_types": [0],
			"required": False
		}, {
			"name": "existing-general-voice",
			"description": "Use existing voice channel instead of creating one. (that doesn't have to be named \"general\")",
			"type": 7,
			"channel_types": [2],
			"required": False
		}],
	guild_ids = guild_ids
)
async def createTournamentCommand(context, **kwargs):
	guild, error = findGuildTournament(context.guild_id, "create a tournament", True)
	if not error is None:
		await context.send(error)
		return
	role = await findOrCreateNameAsync("Tournament Leader", guild.roles, guild.create_role, kwargs.get("existing-leader-role"), colour = Color.dark_gray(), mentionable = True, reason = "Created tournament leader role to show who can use restricted commands in tournaments.")
	if not role in context.author.roles:
		await context.author.add_roles(role)
	category = await findOrCreateNameAsync("Tournament", guild.categories, guild.create_category, kwargs.get("existing-category"))
	infoText, generalText = await findOrCreateNamesAsync({"info": kwargs.get("existing-info-text"), "general": kwargs.get("existing-general-text")}, category.text_channels, category.create_text_channel)
	generalVoice = await findOrCreateNameAsync("General", category.voice_channels, category.create_voice_channel, kwargs.get("existing-general-voice"))

	global tournaments
	tournaments[context.guild_id] = Tournament(guild.id, role.id, category.id, infoText.id, generalText.id, generalVoice.id)
	await context.send(f"Successfully created a tournament, using {infoText.mention} for info, and {generalText.mention} & {generalVoice.mention} for chat.\nYou now have the {role.mention} role.")

@slash.subcommand(
	base = "tournament",
	name = "delete",
	guild_ids = guild_ids
)
async def deleteTournamentCommand(context):
	error = findGuildTournament(context.guild_id, "delete a tournament")[1]
	if not error is None:
		await context.send(error)
		return
	global tournaments
	del tournaments[context.guild_id]
	await context.send("Successfully deleted tournament.")

@slash.subcommand(
	base = "tournament",
	name = "show",
	guild_ids = guild_ids
)
async def tournamentDetailsCommand(context):
	error = findGuildTournament(context.guild_id, "see the ongoing tournament")[1]
	if not error is None:
		await context.send(error)
		return
	await context.send(str(tournaments[context.guild_id]))

colorChoices = []
for i, color in enumerate(colors):
	colorChoices.append({"name": color, "value": i})

@slash.subcommand(
	base = "team",
	name = "create",
	description = "Create team with a new role and channels, or with an existing role/channels.",
	options = [{
			"name": "name",
			"description": "The name of the team.",
			"type": 3,
			"required": True
		}, {
			"name": "color",
			"description": "The color of the team",
			"type": 4,
			"choices": colorChoices,
			"required": False
		}, {
			"name": "existing-team-role",
			"description": "Use existing role instead of creating one. (doesn't have to be named same as team)",
			"type": 8,
			"required": False
		}, {
			"name": "existing-team-text",
			"description": "Use existing text channel instead of creating one. (that doesn't have to be named same as team)",
			"type": 7,
			"channel_types": [0],
			"required": False
		}, {
			"name": "existing-team-voice",
			"description": "Use existing voice channel instead of creating one. (that doesn't have to be named same as team)",
			"type": 7,
			"channel_types": [2],
			"required": False
	}],
	guild_ids = guild_ids
)
async def teamCreateCommand(context, name, **kwargs):
	guild, error = findGuildTournament(context.guild_id, "create a team")
	if not error is None:
		await context.send(error)
		return
	global tournaments
	tournament = tournaments[context.guild_id]
	
	if name in tournament.teams:
		await context.send(f"Can't create team, the name *{name}* is already taken.")
		return
	category = get(guild.categories, id = tournament.categoryId)
	print(tournament.leaderRoleId)
	leaderRole = guild.get_role(tournament.leaderRoleId)
	print(leaderRole)
	if not leaderRole in context.author.roles:
		await context.author.add_roles(leaderRole)
	color = choice(list(colors.values()))
	if "color" in kwargs:
		color = list(colors.values())[kwargs["color"]]
	role = await findOrCreateNameAsync(name, guild.roles, guild.create_role, kwargs.get("existing-team-role"), color = color, mentionable = True, reason = f"Added a role for organizing team \"{name}\".")
	if not role in context.author.roles:
		await context.author.add_roles(role)
	textOverwrites = {
		guild.default_role: PermissionOverwrite(read_messages = False, send_messages = False),
		role: PermissionOverwrite(read_messages = True, send_messages = True)
	}
	teamText = await findOrCreateNameAsync(name, category.text_channels, category.create_text_channel, kwargs.get("existing-team-text"), overwrites = textOverwrites)
	voiceOverwrites = {
		guild.default_role: PermissionOverwrite(connect = False),
		role: PermissionOverwrite(connect = True)
	}
	teamVoice = await findOrCreateNameAsync(name, category.voice_channels, category.create_voice_channel, kwargs.get("existing-team-voice"), overwrites = textOverwrites)
	
	tournament.teams[name] = Team(context.author.id, role.id, teamText.id, teamVoice.id)
	await context.send(f"Successfully created the team *{name}*, with channels {teamText.mention} and {teamVoice.mention}.\nYou are now a tournament leader with the team role {role.mention}.")

@slash.slash(
	name = "join",
	guild_ids = guild_ids
)
async def joinCommand(context):
	guild, error = findGuild(context.guild_id, "join a tournament")
	if not error is None:
		await context.send(error)
		return
	global tournaments
	tournaments[context.guild_id].lobby.append(Player(context.author.id))
	await context.send(f"Successfully added {context.author.mention} to the lobby.")

# Tries to run the client.

try:
	client.run(TOKEN)
except errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")