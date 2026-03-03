import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN non défini dans Railway")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== BASE DE DONNÉES EN MÉMOIRE ======
series_db = {}  
profiles_db = {}  

# Structure series_db :
# {
#   "Nanomancer": {
#       "cover": "url",
#       "va": "url",
#       "salon": channel_id,
#       "roles": {"trad": user_id, "check": None, "clean": None, "edit": None, "qedit": None},
#       "progress": {"trad": 0, "check": 0, "clean": 0, "edit": 0, "qedit": 0}
#   }
# }

# ====== EVENTS ======
@bot.event
async def on_ready():
    guild = discord.Object(id=TON_ID_DE_SERVEUR)
    await bot.tree.sync(guild=guild)
    print("Bot connecté + commandes sync")

# ====== /NEW_SERIE ======
@bot.tree.command(name="new_serie", description="Ajouter une nouvelle série")
async def new_serie(interaction: discord.Interaction, nom: str, cover: str, va: str, salon: discord.TextChannel):
    series_db[nom] = {
        "cover": cover,
        "va": va,
        "salon": salon.id,
        "roles": {"trad": None, "check": None, "clean": None, "edit": None, "qedit": None},
        "progress": {"trad": 0, "check": 0, "clean": 0, "edit": 0, "qedit": 0}
    }
    await interaction.response.send_message(f"Série **{nom}** ajoutée.")

# ====== /ASSIGNEMENT ======
@bot.tree.command(name="assignement", description="Assigner un rôle sur une série")
async def assignement(interaction: discord.Interaction, membre: discord.Member, role: str, serie: str):
    role = role.lower()

    if serie not in series_db:
        await interaction.response.send_message("Série inconnue.")
        return

    if role not in ["trad", "check", "clean", "edit", "qedit"]:
        await interaction.response.send_message("Rôle invalide.")
        return

    # Donner accès au salon
    salon = interaction.guild.get_channel(series_db[serie]["salon"])
    await salon.set_permissions(membre, read_messages=True, send_messages=True)

    # Donner rôle Discord
    discord_role = discord.utils.get(interaction.guild.roles, name=role)
    if discord_role:
        await membre.add_roles(discord_role)

    series_db[serie]["roles"][role] = membre.id

    # Profil utilisateur
    if membre.id not in profiles_db:
        profiles_db[membre.id] = {"roles": set(), "chapters": 0, "series": set()}
    profiles_db[membre.id]["roles"].add(role)
    profiles_db[membre.id]["series"].add(serie)

    await interaction.response.send_message(f"{membre.mention} est maintenant **{role}** sur **{serie}**.")

# ====== /INFOS ======
@bot.tree.command(name="infos", description="Voir infos d'une série")
async def infos(interaction: discord.Interaction, serie: str):
    if serie not in series_db:
        await interaction.response.send_message("Série inconnue.")
        return

    s = series_db[serie]

    msg = (
        f"**{serie}**\n"
        f"Cover : {s['cover']}\n"
        f"VA : {s['va']}\n\n"
        f"Trad : {mention_user(s['roles']['trad'])} ({s['progress']['trad']})\n"
        f"Check : {mention_user(s['roles']['check'])} ({s['progress']['check']})\n"
        f"Clean : {mention_user(s['roles']['clean'])} ({s['progress']['clean']})\n"
        f"Edit : {mention_user(s['roles']['edit'])} ({s['progress']['edit']})\n"
        f"QEdit : {mention_user(s['roles']['qedit'])} ({s['progress']['qedit']})\n"
    )

    await interaction.response.send_message(msg)

def mention_user(user_id):
    return f"<@{user_id}>" if user_id else "Non assigné"

# ====== /PROFIL ======
@bot.tree.command(name="profil", description="Voir profil d'un membre")
async def profil(interaction: discord.Interaction, membre: discord.Member):
    if membre.id not in profiles_db:
        await interaction.response.send_message("Aucune donnée.")
        return

    p = profiles_db[membre.id]
    roles = ", ".join(p["roles"])
    series = ", ".join(p["series"])

    msg = (
        f"Profil de {membre.mention}\n"
        f"Rôles : {roles}\n"
        f"Chapitres faits : {p['chapters']}\n"
        f"Séries : {series}"
    )
    await interaction.response.send_message(msg)

# ====== /HELP ======
@bot.tree.command(name="help", description="Voir les commandes")
async def help_cmd(interaction: discord.Interaction):
    msg = (
        "/new_serie\n"
        "/assignement\n"
        "/infos\n"
        "/profil\n"
        "/announce"
    )
    await interaction.response.send_message(msg)

# ====== /ANNOUNCE ======
@bot.tree.command(name="announce", description="Annoncer un nouveau chapitre")
async def announce(interaction: discord.Interaction, serie: str, lien: str):
    await interaction.response.send_message(f"@everyone **{serie}** nouveau chapitre !\n{lien}")

bot.run(TOKEN)



