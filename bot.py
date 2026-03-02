import os
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.environ.get("DISCORD_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))

if TOKEN is None or GUILD_ID is None:
    raise ValueError("Il faut définir DISCORD_TOKEN et GUILD_ID dans les variables d'environnement !")

intents = discord.Intents.default()
intents.members = True  # nécessaire pour assigner des rôles

client = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLES = ["Trad", "Check", "Clean", "Edit", "Qedit"]

@client.event
async def on_ready():
    print(f"{client.user} connecté !")
    guild = discord.Object(id=GUILD_ID)
    await client.tree.sync(guild=guild)
    print(f"Commandes synchronisées sur le serveur {GUILD_ID}")

# --------------------------
# Commande /infos
# --------------------------
@client.tree.command(name="infos", description="Affiche les infos du bot", guild=discord.Object(id=GUILD_ID))
async def infos(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Bot opérationnel ✅\nUtilisateur: {interaction.user.mention}"
    )

# --------------------------
# Commande /assignement
# --------------------------
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
async def assignement(interaction: discord.Interaction, role: str, serie: discord.TextChannel, user: discord.Member):
    if role not in ALLOWED_ROLES:
        await interaction.response.send_message(
            f"Rôle invalide. Choisis parmi: {', '.join(ALLOWED_ROLES)}", ephemeral=True
        )
        return

    discord_role = discord.utils.get(interaction.guild.roles, name=role)
    if not discord_role:
        await interaction.response.send_message(f"Le rôle `{role}` n'existe pas sur ce serveur.", ephemeral=True)
        return

    await user.add_roles(discord_role)
    await interaction.response.send_message(
        f"{user.mention} a reçu le rôle `{role}` pour la série {serie.mention} ✅"
    )

client.run(TOKEN)
