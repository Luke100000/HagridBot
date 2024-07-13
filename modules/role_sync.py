import datetime
import os

import requests
from discord import Interaction, Member, Guild
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
HAGRID_SECRET = os.getenv("HAGRID_SECRET")

url = "https://discord.com/api/v10/applications/1072981047890939985/commands"

headers = {"Authorization": "Bot " + TOKEN}

LINK_API_IN_USE = False

SYNC_ROLES = {
    "Iron",
    "Gold",
    "Diamond",
    "Moderator",
}


def register_command(command: dict):
    requests.post(
        url,
        timeout=5.0,
        headers=headers,
        json=command,
    )


register_command(
    {
        "name": "link",
        "type": 1,
        "description": "Link your Minecraft username",
        "options": [
            {"name": "username", "description": "Username", "type": 3, "required": True}
        ],
    }
)

register_command(
    {
        "name": "unlink",
        "type": 1,
        "description": "Unlink a Minecraft username",
        "options": [
            {
                "name": "username",
                "description": "Username",
                "type": 3,
                "required": False,
            }
        ],
    }
)

register_command({"name": "sync", "type": 1, "description": "Sync user roles"})

URL = "https://api.conczin.net"


async def delete_user(interaction: Interaction, username: str):
    response = requests.delete(
        URL + f"/v1/minecraft/{interaction.guild.id}/{username}",
        timeout=5.0,
        params={"token": HAGRID_SECRET},
    )
    if "error" in response.json():
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message("Something went all wonky.")
    else:
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message("Username's been unlinked, it has.")


def get_roles(member):
    return [role.name for role in member.roles if role.name in SYNC_ROLES]


def create_member(member: Member, username: str = None):
    return requests.post(
        URL + f"/v1/minecraft/{member.guild.id}/{member.id}",
        params={
            "token": HAGRID_SECRET,
            "discord_username": member.display_name,
            "minecraft_username": username,
            "roles": ", ".join(get_roles(member)),
        },
        timeout=5.0,
    )


def update_member(member: Member):
    return requests.put(
        URL + f"/v1/minecraft/{member.guild.id}/{member.id}",
        timeout=5.0,
        params={
            "token": HAGRID_SECRET,
            "discord_username": member.display_name,
            "roles": ", ".join(get_roles(member)),
        },
    )


last_execution_time = None


async def sync_users(guild: Guild, force: bool = False):
    global LINK_API_IN_USE
    if not LINK_API_IN_USE:
        return

    global last_execution_time
    current_time = datetime.datetime.now()

    if (
        last_execution_time is None
        or (current_time - last_execution_time).total_seconds() >= 3600
        or force
    ):
        for member in guild.members:
            if len(get_roles(member)) > 0:
                update_member(member)
        last_execution_time = current_time


async def role_sync_command(interaction: Interaction):
    if interaction.data["name"] == "sync":
        await sync_users(interaction.guild, True)
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message("Done!")

    if interaction.data["name"] == "link":
        global LINK_API_IN_USE
        LINK_API_IN_USE = True

        # noinspection PyTypeChecker
        username = interaction.data["options"][0]["value"]

        response = create_member(interaction.user, username)

        translations = {
            "Discord account already linked.": "Discord account's already linked, ain't it? Unlink your old Minecraft account!",
            "Minecraft account already linked.": "Minecraft account's already linked, ain't it? Unlink it first!",
        }

        data = response.json()
        if "error" in data:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(
                translations[data["error"]]
                if data["error"] in translations
                else data["error"]
            )
        else:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message("Username's been linked, it has.")

    if interaction.data["name"] == "unlink":
        if "options" in interaction.data:
            if interaction.user.guild_permissions.administrator:
                # noinspection PyTypeChecker
                username = interaction.data["options"][0]["value"]
                await delete_user(interaction, username)
            else:
                # noinspection PyUnresolvedReferences
                await interaction.response.send_message("Yer no admin, sorry")
        else:
            await delete_user(interaction, str(interaction.user.id))
