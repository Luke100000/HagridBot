from discord import Interaction, Message, app_commands

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


def _fetch_guild_rows(guild: str) -> list[tuple[str, int]]:
    rows = fetch_all(
        "SELECT group_name, count FROM stats WHERE guild = ? ORDER BY count DESC",
        (guild,),
    )
    return [(str(row["group_name"]), int(row["count"])) for row in rows]


def format_stats(guild: str | None = None, top_n: int = 5) -> str:
    if guild:
        rows = _fetch_guild_rows(guild)
        if not rows:
            return f"No stats found for guild '{guild}'."

        lines = [f"# {guild}"]
        for group, count in rows:
            lines.append(f"* {group.replace('_', ' ')}: {count}")
        return "\n".join(lines)

    rows = fetch_all(
        "SELECT guild, group_name, count FROM stats ORDER BY guild ASC, count DESC"
    )
    if not rows:
        return "No usage stats collected yet."

    grouped: dict[str, list[tuple[str, int]]] = {}
    for row in rows:
        g = str(row["guild"])
        grouped.setdefault(g, []).append((str(row["group_name"]), int(row["count"])))

    lines = []
    for guild_name in sorted(grouped.keys()):
        guild_rows = grouped[guild_name]
        top = guild_rows[:top_n]
        other = sum(count for _, count in guild_rows[top_n:])
        compact = ", ".join(f"{name.replace('_', ' ')}: {count}" for name, count in top)
        if other > 0:
            compact = f"{compact}, other: {other}"
        lines.append(f"- {guild_name}: {compact}")
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
            text = format_stats(guild=guild)
            await interaction.response.send_message(
                f"```md\n{text}\n```",
                ephemeral=True,
            )


async def setup(tree: app_commands.CommandTree) -> StatsModule:
    return StatsModule(tree)
