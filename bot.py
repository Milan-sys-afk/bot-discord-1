import discord
from discord import app_commands
from discord.ext import commands
import os

# ----- CONFIGURATION -----
# Remplace GUILD_ID par l'ID de ton serveur
GUILD_ID = 1477748649642692709

# Rôles autorisés pour /assignement
ALLOWED_ROLES = ["Trad", "Check", "Clean", "Edit", "Qedit"]

# Token Railway
TOKEN = os.environ.get("DISCORD_TOKEN")  # Assure-toi que Railway a bien la variable DISCORD_TOKEN

# ----- INTENTS -----
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

# ----- COMMAND TREE -----
@client.event
async def on_ready():
    await client.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Connecté en tant que {client.user}")

# ----- /infos -----
@client.tree.command(
    name="infos",
    description="Affiche des informations sur le bot",
    guild=discord.Object(id=GUILD_ID)
)
async def infos(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Infos",
        description="Je suis le bot principal pour gérer les assignements et infos des séries.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Commandes disponibles", value="/infos, /assignement")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ----- /assignement -----
@client.tree.command(
    name="assignement",
    description="Assigne un rôle à un utilisateur pour une série",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    role="Rôle à assigner",
    serie="Salon texte de la série",
    user="Utilisateur à assigner"
)
@app_commands.choices(role=[app_commands.Choice(name=r, value=r) for r in ALLOWED_ROLES])
async def assignement(
    interaction: discord.Interaction, 
    role: app_commands.Choice[str], 
    serie: discord.TextChannel, 
    user: discord.Member
):
    discord_role = discord.utils.get(interaction.guild.roles, name=role.value)
    if not discord_role:
        await interaction.response.send_message(f"Le rôle `{role.value}` n'existe pas sur ce serveur.", ephemeral=True)
        return

    try:
        await user.add_roles(discord_role)
        await interaction.response.send_message(
            f"{user.mention} a reçu le rôle `{role.value}` pour la série {serie.mention} ✅"
        )
    except discord.Forbidden:
        await interaction.response.send_message("Je n'ai pas la permission d'ajouter ce rôle.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Erreur: {e}", ephemeral=True)

# ----- RUN BOT -----
if TOKEN is None:
    print("Erreur: DISCORD_TOKEN non défini dans les variables d'environnement.")
else:
    client.run(TOKEN)
