
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL = os.environ["DISCORD_CHANNEL_ID"]
SERVER = os.getenv("MC_SERVER_ADDRESS", "Starfall-t6RL.aternos.me")
INVITE = "https://discord.gg/fXNwNr47"
API = "https://discord.com/api/v10"


def get_json(url, headers=None, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, method=method, headers=headers or {}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def discord(method, path, body=None):
    return get_json(
        API + path,
        {
            "Authorization": "Bot " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "StarfallStatusBot/1.0",
        },
        method,
        body,
    )


def main():
    status_url = (
        "https://api.mcsrvstat.us/bedrock/3/"
        + urllib.parse.quote(SERVER, safe=".:")
    )
    data = get_json(status_url, {"User-Agent": "StarfallStatusBot/1.0"})

    if "online" not in data:
        raise RuntimeError("Não foi possível verificar o servidor.")

    online = bool(data["online"])

    try:
        with open("state.json", encoding="utf-8") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {"last_online": None, "message_id": None}

    if online:
        players = data.get("players") or {}
        count = players.get("online", "?")
        maximum = players.get("max", "?")
        status = "🟢 ONLINE"
        description = "O Starfall está aberto! Venha jogar."
        color = 0x22C55E
        player_text = f"{count}/{maximum}"
    else:
        status = "🔴 OFFLINE"
        description = "O servidor está desligado ou iniciando."
        color = 0xEF4444
        player_text = "—"

    embed = {
        "title": "🌌 STARFALL | STATUS",
        "description": description,
        "color": color,
        "fields": [
            {"name": "Estado", "value": status, "inline": True},
            {"name": "Jogadores", "value": player_text, "inline": True},
            {"name": "Edição", "value": "Minecraft Bedrock", "inline": True},
            {"name": "Endereço", "value": f"`{SERVER}`", "inline": False},
        ],
        "footer": {
            "text": "Atualizado em "
            + datetime.now(timezone.utc).strftime("%d/%m %H:%M UTC")
        },
        "url": INVITE,
    }

    message_id = state.get("message_id")
    if message_id:
        try:
            discord(
                "PATCH",
                f"/channels/{CHANNEL}/messages/{message_id}",
                {"embeds": [embed]},
            )
        except Exception:
            message_id = None

    if not message_id:
        message = discord(
            "POST",
            f"/channels/{CHANNEL}/messages",
            {"embeds": [embed]},
        )
        message_id = message["id"]

    if online and state["last_online"] is False:
        discord(
            "POST",
            f"/channels/{CHANNEL}/messages",
            {
                "content": (
                    "🎉 @here **O STARFALL ESTÁ ONLINE!**\n"
                    f"IP: `{SERVER}`\n{INVITE}"
                ),
                "allowed_mentions": {"parse": ["here"]},
            },
        )

    state["last_online"] = online
    state["message_id"] = message_id

    with open("state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("Starfall:", status)


if __name__ == "__main__":
    main()
  
