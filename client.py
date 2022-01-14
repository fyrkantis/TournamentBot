# External Libraries
import os
from dotenv import load_dotenv

import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = discord.Client()

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

slash = SlashCommand(client, sync_commands = True)
guild_ids = [732240720487776356]

@slash.subcommand(
	base = "create",
	name = "channels",
	description = "Creates all necessary text and voice channels for the bot to function, if needed.",
	guild_ids = guild_ids)
async def createChannels(context):
	guildId = context.guild_id
	if guildId is None:
		await context.send("Sorry, can't create channels in DMs.")
		return
	guild = None
	for joinedGuild in client.guilds:
		if joinedGuild.id == guildId:
			guild = joinedGuild
			break
	if guild is None:
		await context.send("You need to invite Tournament Bot to create channels.\nInvite link: https://discord.com/api/oauth2/authorize?client_id=931495315834548244&permissions=285379664&scope=bot%20applications.commands")
		return
	
	# Finds or creates a category named "tournament".
	category = None
	for guildCategory in guild.categories:
		if guildCategory.name.lower() == "tournament":
			category = guildCategory
	if category is None:
		category = await guild.create_category("tournament")
	
	await context.send(f"Successfully created the category \"{category.name}\".")

try:
	client.run(TOKEN)
except discord.errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")