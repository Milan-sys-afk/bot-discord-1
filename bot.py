import os
print("ENV:", os.environ)

TOKEN = os.getenv("DISCORD_TOKEN")
print("TOKEN:", TOKEN)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN absent")



