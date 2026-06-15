from discord import Interaction, Message, app_commands

from app.permissions import has_permission, send_permission_denied
from app.storage import execute, fetch_all


def stat(message: Message, group: str) -> None:
    guild = message.guild.name
    execute(
        """
        INSERT INTO stats (guild, group_name, count)
        VALUES (?, ?, 1)
        ON CONFLICT(guild, group_name)
        DO UPDATE SET count = count + 1
        """,
        (guild, group),
    )


def _fetch_guild_rows(guild: str, limit: int) -> list[tuple[str, int]]:
    rows = fetch_all(
        """
        SELECT group_name, count
        FROM stats
        WHERE guild = ?
        ORDER BY count DESC
        LIMIT ?
        """,
        (guild, limit),
    )
    return [(str(row["group_name"]), int(row["count"])) for row in rows]


def format_stats(guild: str | None = None, top_n: int = 10) -> str:
    if guild:
        rows = _fetch_guild_rows(guild, top_n)
        if not rows:
            return f"No stats found for guild '{guild}'."

        lines = [f"# Top {min(top_n, len(rows))} in {guild}"]
        for group, count in rows:
            lines.append(f"* {group.replace('_', ' ')}: {count}")
        return "\n".join(lines)

    rows = fetch_all(
        """
        SELECT guild, group_name, count
        FROM stats
        ORDER BY count DESC
        LIMIT ?
        """,
        (top_n,),
    )
    if not rows:
        return "No usage stats collected yet."

    lines = [f"# Top {len(rows)} usage stats"]
    for row in rows:
        guild_name = str(row["guild"])
        group_name = str(row["group_name"]).replace("_", " ")
        count = int(row["count"])
        lines.append(f"* {guild_name} / {group_name}: {count}")
    return "\n".join(lines)


class StatsModule:
    def __init__(self, tree: app_commands.CommandTree):
        self.tree = tree
        self._register_commands()

    def _register_commands(self) -> None:
        @self.tree.command(name="stats", description="Show bot usage stats.")
        async def stats_command(
            interaction: Interaction,
            guild: str | None = None,
        ) -> None:
            guild_id = interaction.guild.id if interaction.guild else None
            if not has_permission(interaction.user.id, guild_id, 2):
                await send_permission_denied(interaction, 2)
                return

            text = format_stats(guild=guild)
            await interaction.response.send_message(
                f"```md\n{text}\n```",
                ephemeral=True,
            )


async def setup(tree: app_commands.CommandTree) -> StatsModule:
    return StatsModule(tree)
