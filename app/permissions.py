import discord
from discord import app_commands

from app.storage import execute, fetch_one

CONCZIN_USER_ID = 200587604582727682
DEFAULT_LEVEL = 0
MIN_LEVEL = 0
MAX_LEVEL = 3


def clamp_permission_level(level: int) -> int:
    return max(MIN_LEVEL, min(MAX_LEVEL, int(level)))


def get_user_permission_level(user_id: int) -> int:
    if user_id == CONCZIN_USER_ID:
        default = MAX_LEVEL
    else:
        default = DEFAULT_LEVEL

    row = fetch_one(
        "SELECT level FROM user_permissions WHERE user_id = ?",
        (user_id,),
    )
    if row is None:
        return default
    return int(row["level"])


def get_guild_permission_level(guild_id: int | None) -> int:
    if guild_id is None:
        return DEFAULT_LEVEL

    row = fetch_one(
        "SELECT level FROM guild_permissions WHERE guild_id = ?",
        (guild_id,),
    )
    if row is None:
        return DEFAULT_LEVEL
    return int(row["level"])


def get_effective_permission_level(user_id: int, guild_id: int | None = None) -> int:
    return max(get_user_permission_level(user_id), get_guild_permission_level(guild_id))


def has_permission(user_id: int, guild_id: int | None, required_level: int) -> bool:
    return get_effective_permission_level(user_id, guild_id) >= required_level


def set_user_permission_level(user_id: int, level: int) -> None:
    level = clamp_permission_level(level)
    if level == DEFAULT_LEVEL:
        execute("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
        return

    execute(
        """
        INSERT INTO user_permissions (user_id, level)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET level = excluded.level
        """,
        (user_id, level),
    )


def set_guild_permission_level(guild_id: int, level: int) -> None:
    level = clamp_permission_level(level)
    if level == DEFAULT_LEVEL:
        execute("DELETE FROM guild_permissions WHERE guild_id = ?", (guild_id,))
        return

    execute(
        """
        INSERT INTO guild_permissions (guild_id, level)
        VALUES (?, ?)
        ON CONFLICT(guild_id)
        DO UPDATE SET level = excluded.level
        """,
        (guild_id, level),
    )


async def send_permission_denied(
    interaction: discord.Interaction,
    required_level: int,
) -> None:
    message = f"Ye need permission level {required_level} for that."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class PermissionModule:
    def __init__(self, tree: app_commands.CommandTree):
        self.tree = tree
        self._register_commands()

    def _register_commands(self) -> None:
        @self.tree.command(
            name="permission",
            description="Show or set a user's Hagrid permission level.",
        )
        async def permission_command(
            interaction: discord.Interaction,
            user: discord.User,
            level: app_commands.Range[int, MIN_LEVEL, MAX_LEVEL] | None = None,
        ) -> None:
            caller_level = get_user_permission_level(interaction.user.id)

            if level is None:
                target_level = get_user_permission_level(user.id)
                await interaction.response.send_message(
                    f"{user.mention} has permission level {target_level}.",
                    ephemeral=True,
                )
                return

            level = int(level)
            target_level = get_user_permission_level(user.id)
            if target_level > caller_level:
                await interaction.response.send_message(
                    f"Ye can't change someone above yer own level ({caller_level}).",
                    ephemeral=True,
                )
                return

            if level > caller_level:
                await interaction.response.send_message(
                    f"Ye can only set permission levels up to yer own level ({caller_level}).",
                    ephemeral=True,
                )
                return

            set_user_permission_level(user.id, level)
            if level == DEFAULT_LEVEL:
                message = f"Removed {user.mention} from the permission database."
            else:
                message = f"Set {user.mention} to permission level {level}."
            await interaction.response.send_message(message, ephemeral=True)

        @self.tree.command(
            name="guildpermission",
            description="Show or set this guild's Hagrid permission level.",
        )
        async def guild_permission_command(
            interaction: discord.Interaction,
            level: app_commands.Range[int, MIN_LEVEL, MAX_LEVEL] | None = None,
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This 'ere command only works inside a proper guild, it does.",
                    ephemeral=True,
                )
                return

            caller_level = get_user_permission_level(interaction.user.id)
            if caller_level < MAX_LEVEL:
                await send_permission_denied(interaction, MAX_LEVEL)
                return

            if level is None:
                guild_level = get_guild_permission_level(interaction.guild.id)
                await interaction.response.send_message(
                    f"{interaction.guild.name} has permission level {guild_level}.",
                    ephemeral=True,
                )
                return

            level = int(level)
            set_guild_permission_level(interaction.guild.id, level)
            if level == DEFAULT_LEVEL:
                message = "Removed this guild from the permission database."
            else:
                message = f"Set this guild to permission level {level}."
            await interaction.response.send_message(message, ephemeral=True)
