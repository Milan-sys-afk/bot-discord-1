import discord
from discord.ext import commands
import asyncio
import json
import requests
import os
from discord import app_commands

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# mapping roles d’étapes
ROLES = {
    "Trad": 1477773359545585704,
    "Check": 1477773414155423784,
    "Clean": 1477773442567901318,
    "Edit": 1477773468287111421,
    "QEdit": 1477773546817327125
}

# fichier JSON local pour suivre assignations et derniers chapitres
DATA_FILE = "chapters.json"

# charger ou créer la DB
try:
    with open(DATA_FILE, "r") as f:
        CHAPTERS = json.load(f)
except:
    CHAPTERS = {}

# ===== CLIENT =====
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ===== FONCTIONS =====
def get_chapters_status():
    """
    Récupère le statut actuel des chapitres depuis le site / API JSON
    Retour : {"SerieA": {"Chapitre1": {"Trad": "Alice", ...}}}
    """
    try:
        r = requests.get("https://tonsite.xyz/api/chapters_status")  # à adapter
        r.raise_for_status()
        return r.json()
    except:
        return {}

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(CHAPTERS, f, indent=4)

# ===== LOOP D'ANNONCE =====
async def check_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while True:
        chapters_status = get_chapters_status()
        for serie, chap_data in chapters_status.items():
            if serie not in CHAPTERS:
                CHAPTERS[serie] = {}
            for chap, status in chap_data.items():
                last_status = CHAPTERS[serie].get(chap, {}).get("status")
                if last_status != status:
                    CHAPTERS[serie][chap] = {"status": status, "assigned": chap_data[chap].get("assigned", {})}
                    # ping le rôle correspondant
                    role_id = ROLES.get(status)
                    if role_id:
                        await channel.send(f"<@&{role_id}> Chapitre {chap} de {serie} prêt pour **{status}**")
        save_db()
        await asyncio.sleep(300)  # toutes les 5 min

# ===== SLASH COMMANDS =====
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot Ping Chapitres connecté : {client.user}")
    client.loop.create_task(check_loop())

# /infos <serie>
@tree.command(name="infos", description="Affiche le dernier chapitre et responsables", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(serie="Nom de la série")
async def infos(interaction: discord.Interaction, serie: str):
    if serie not in CHAPTERS:
        await interaction.response.send_message("Série introuvable !", ephemeral=True)
        return
    # trouver dernier chapitre pour chaque étape
    embed = discord.Embed(title=f"Infos {serie}", color=0x00ff00)
    for step in ["Trad", "Check", "Clean", "Edit", "QEdit"]:
        chap = None
        user = "N/A"
        for c, data in CHAPTERS[serie].items():
            if data.get("status") == step:
                chap = c
                user = ", ".join(data.get("assigned", {}).get(step, [])) if data.get("assigned") else "N/A"
        embed.add_field(name=step, value=f"{chap} → {user}", inline=False)
    await interaction.response.send_message(embed=embed)

# /assignment <role> <serie> <user>
@tree.command(name="assignment", description="Assigne un membre à un rôle sur une série", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(role="Rôle à assigner", serie="Nom de la série", user="Membre à assigner")
async def assignment(interaction: discord.Interaction, role: str, serie: str, user: discord.Member):
    if serie not in CHAPTERS:
        CHAPTERS[serie] = {}
    # assignation dans JSON
    for chap, data in CHAPTERS[serie].items():
        if "assigned" not in data:
            data["assigned"] = {}
        if role not in data["assigned"]:
            data["assigned"][role] = []
        if user.name not in data["assigned"][role]:
            data["assigned"][role].append(user.name)
    save_db()
    # assigner rôle Discord
    role_id = ROLES.get(role)
    if role_id:
        discord_role = interaction.guild.get_role(role_id)
        if discord_role:
            await user.add_roles(discord_role)
    await interaction.response.send_message(f"{user.mention} assigné au rôle {role} pour {serie} ✅")

# ===== ASSIGNATION PAR REACTION =====
@client.event
async def on_raw_reaction_add(payload):
    # Exemple : message spécifique pour assigner rôle série
    # mapping : emoji -> rôle série
    EMOJI_ROLE = {"🔵": "SerieA", "🟢": "SerieB"}  # à adapter
    if payload.emoji.name in EMOJI_ROLE:
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_name = EMOJI_ROLE[payload.emoji.name]
        # créer rôle série si n'existe pas
        discord_role = discord.utils.get(guild.roles, name=role_name)
        if not discord_role:
            discord_role = await guild.create_role(name=role_name)
        await member.add_roles(discord_role)

@client.event
async def on_raw_reaction_remove(payload):
    EMOJI_ROLE = {"🔵": "SerieA", "🟢": "SerieB"}  # même mapping
    if payload.emoji.name in EMOJI_ROLE:
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_name = EMOJI_ROLE[payload.emoji.name]
        discord_role = discord.utils.get(guild.roles, name=role_name)
        if discord_role:
            await member.remove_roles(discord_role)

# ===== RUN =====

client.run(TOKEN)

