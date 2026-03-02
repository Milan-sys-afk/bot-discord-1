import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])

# Intents
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Rôles autorisés
ROLES_CHOICES = ["Trad", "Check", "Clean", "Edit", "Qedit"]

# Fonction pour récupérer les salons séries
def get_series_channels(guild: discord.Guild):
    return [c for c in guild.text_channels if c.name.startswith("serie-")]

# Commande /infos
@tree.command(name="infos", description="Affiche les infos du bot ou du serveur")
async def infos(interaction: discord.Interaction):
    await interaction.response.send_message(f"Bot : {bot.user.name}\nServeur : {interaction.guild.name}\nTotal membres : {interaction.guild.member_count}")

# Commande /assignement
@tree.command(name="assignement", description="Assigner un rôle et une série à un utilisateur")
@app_commands.describe(
    role="Rôle à assigner",
    series="Salon de la série",
    user="Utilisateur à assigner"
)
@app_commands.choices(role=[app_commands.Choice(name=r, value=r) for r in ROLES_CHOICES])
async def assignement(interaction: discord.Interaction, role: app_commands.Choice[str], series: str, user: discord.Member):
    guild = interaction.guild
    if series not in [c.name for c in get_series_channels(guild)]:
        await interaction.response.send_message(f"Erreur : le salon `{series}` n'existe pas.", ephemeral=True)
        return

    discord_role = discord.utils.get(guild.roles, name=role.value)
    if not discord_role:
        await interaction.response.send_message(f"Erreur : le rôle `{role.value}` n'existe pas sur le serveur.", ephemeral=True)
        return

    await user.add_roles(discord_role)
    await interaction.response.send_message(f"{user.mention} a été assigné au rôle `{role.value}` pour la série `{series}`.")

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{bot.user} connecté et commandes synchronisées sur le serveur {GUILD_ID}!")

bot.run(TOKEN)


