import os
import json
import discord
from discord import app_commands, Interaction
from discord.ext import commands


# Charger le token

TOKEN = os.getenv("DISCORD_TOKEN_BOT1")
if TOKEN is None:
    raise ValueError("DISCORD_TOKEN n'est pas défini dans Railway")
# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

# Fichier JSON partagé avec Bot Avancement
DATA_FILE = "data_avancement.json"

staff_roles = ["trad", "check", "clean", "edit", "qedit"]

# ---------------- UTILITAIRES ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def role_valid(role_name):
    return role_name.lower() in staff_roles

# ---------------- COMMANDES ----------------
@tree.command(name="New_série", description="Ajouter une nouvelle série")
@app_commands.describe(nom="Nom de la série", cover="Lien de la cover", va="Lien de la VA")
async def new_serie(interaction: Interaction, nom: str, cover: str, va: str):
    data = load_data()
    if nom in data:
        await interaction.response.send_message(f"La série **{nom}** existe déjà.", ephemeral=True)
        return

    data[nom] = {
        "cover": cover,
        "va": va,
        "members": {},   # user_id par rôle
        "current_chap": 1,
        "chapters": {}
    }
    save_data(data)
    await interaction.response.send_message(f"Série **{nom}** ajoutée avec succès !")

@tree.command(name="assignement", description="Assigner un membre à un rôle sur une série")
@app_commands.describe(role="Rôle à assigner", serie="Salon textuel de la série", utilisateur="Utilisateur à assigner")
async def assignement(interaction: Interaction, role: str, serie: discord.TextChannel, utilisateur: discord.Member):
    role_lower = role.lower()
    if not role_valid(role_lower):
        await interaction.response.send_message(f"Rôle invalide. Choisis parmi : {', '.join(staff_roles)}.", ephemeral=True)
        return

    data = load_data()
    serie_name = serie.name
    if serie_name not in data:
        await interaction.response.send_message(f"La série **{serie_name}** n'existe pas.", ephemeral=True)
        return

    # Ajouter le membre au rôle
    data[serie_name]["members"][role_lower] = utilisateur.id
    save_data(data)

    # Permissions du salon
    perms = serie.overwrites_for(utilisateur)
    perms.read_messages = True
    perms.send_messages = True
    perms.view_channel = True
    await serie.set_permissions(utilisateur, overwrite=perms)

    # Ajouter rôle Discord
    discord_role = discord.utils.get(interaction.guild.roles, name=role.capitalize())
    if discord_role:
        await utilisateur.add_roles(discord_role)

    await interaction.response.send_message(f"{utilisateur.mention} assigné en **{role_lower.capitalize()}** pour la série **{serie_name}** !")

@tree.command(name="infos", description="Obtenir les infos d'une série")
@app_commands.describe(serie="Salon textuel de la série")
async def infos(interaction: Interaction, serie: discord.TextChannel):
    data = load_data()
    serie_name = serie.name
    if serie_name not in data:
        await interaction.response.send_message(f"La série **{serie_name}** n'existe pas.", ephemeral=True)
        return

    serie_data = data[serie_name]
    embed = discord.Embed(title=f"Infos sur {serie_name}", description=f"[VA]({serie_data['va']})", color=0x00ff00)
    embed.set_thumbnail(url=serie_data["cover"])
    for r in staff_roles:
        member_id = serie_data.get("members", {}).get(r)
        if member_id:
            member = interaction.guild.get_member(member_id)
            embed.add_field(name=r.capitalize(), value=member.mention if member else "N/A", inline=True)
        else:
            embed.add_field(name=r.capitalize(), value="N/A", inline=True)
    embed.add_field(name="Chapitre actuel", value=str(serie_data.get("current_chap", 1)))
    await interaction.response.send_message(embed=embed)

@tree.command(name="profil", description="Voir tes rôles et séries")
async def profil(interaction: Interaction):
    user = interaction.user
    data = load_data()
    msg = f"Profil de {user.mention} :\n"
    for serie_name, serie_data in data.items():
        user_roles = [r.capitalize() for r, uid in serie_data.get("members", {}).items() if uid == user.id]
        if user_roles:
            msg += f"- {serie_name} : {', '.join(user_roles)} (Chapitre {serie_data.get('current_chap',1)})\n"
    if msg.strip() == f"Profil de {user.mention} :":
        msg += "Aucun rôle assigné."
    await interaction.response.send_message(msg)

@tree.command(name="help", description="Voir les commandes disponibles")
async def help(interaction: Interaction):
    cmds = [
        "/New_série nom cover va",
        "/assignement role série utilisateur",
        "/infos série",
        "/profil",
        "/help"
    ]
    await interaction.response.send_message("Commandes disponibles :\n" + "\n".join(cmds))

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {client.user}")

client.run(TOKEN)



