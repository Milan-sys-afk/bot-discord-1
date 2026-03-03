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
@app_commands.command(name="assignement", description="Assigner un membre à une série")
@app_commands.describe(role="Rôle à donner", user="Utilisateur à assigner", salon="Salon de la série")
@app_commands.choices(role=[
    app_commands.Choice(name="Trad", value="Trad"),
    app_commands.Choice(name="Check", value="Check"),
    app_commands.Choice(name="Clean", value="Clean"),
    app_commands.Choice(name="Edit", value="Edit"),
    app_commands.Choice(name="Qedit", value="Qedit"),
])
async def assignement(interaction: discord.Interaction, role: app_commands.Choice[str], user: discord.Member, salon: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)  # Empêche l'expiration

    guild = interaction.guild
    role_name = role.value
    serie_role = discord.utils.get(guild.roles, name=role_name)
    if not serie_role:
        await interaction.followup.send(f"❌ Le rôle {role_name} n'existe pas !", ephemeral=True)
        return

    try:
        # Ajouter le rôle staff
        await user.add_roles(serie_role)

        # Ajouter le rôle de série (assume le rôle du salon a le même nom que le salon)
        serie_role_salon = discord.utils.get(guild.roles, name=salon.name)
        if serie_role_salon:
            await user.add_roles(serie_role_salon)

        # Permissions du salon pour le membre
        overwrite = discord.PermissionOverwrite()
        overwrite.view_channel = True
        overwrite.send_messages = True
        await salon.set_permissions(user, overwrite=overwrite)

        await interaction.followup.send(f"✅ {user.mention} a été assigné avec le rôle {role_name} sur {salon.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Je n'ai pas la permission d'ajouter ce rôle ou de modifier le salon.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur inconnue : {e}", ephemeral=True)

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




