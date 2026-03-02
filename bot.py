import os
import discord
from discord.ext import commands
from discord import app_commands

# Récupération des variables d'environnement directement
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # ID du serveur Discord

if TOKEN is None or GUILD_ID is None:
    raise ValueError("Token ou GUILD_ID manquant ! Vérifie tes variables d'environnement.")

# Intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Pour assigner des rôles et mentionner des utilisateurs

client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree  # utiliser le tree déjà associé au client

# --- COMMANDES ---

# /infos
@tree.command(name="infos", description="Obtenir des infos sur le projet")
async def infos(interaction: discord.Interaction):
    await interaction.response.send_message("Voici les infos du projet.")

# /assignement
@tree.command(name="assignement", description="Assigner un rôle et une série")
@app_commands.choices(role=[
    app_commands.Choice(name="Trad", value="Trad"),
    app_commands.Choice(name="Check", value="Check"),
    app_commands.Choice(name="Clean", value="Clean"),
    app_commands.Choice(name="Edit", value="Edit"),
    app_commands.Choice(name="Qedit", value="Qedit")
])
@app_commands.describe(salon="Nom du salon de la série", user="Utilisateur à assigner")
async def assignement(interaction: discord.Interaction, role: app_commands.Choice[str], salon: str, user: discord.Member):
    # Vérifie que le salon existe sur le serveur
    discord_salon = discord.utils.get(interaction.guild.text_channels, name=salon)
    if not discord_salon:
        await interaction.response.send_message(f"Le salon `{salon}` n'existe pas.", ephemeral=True)
        return
    
    await interaction.response.send_message(f"Assigné {role.value} pour {discord_salon.mention} à {user.mention}")

# --- EVENT READY ---
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print(f"{client.user} connecté. Commandes synchronisées pour le serveur {GUILD_ID}.")

# Lancer le bot
client.run(TOKEN)
