import math
import time
from typing import Optional

import discord
from discord import app_commands

from app import config
from app.storage import execute, fetch_all, fetch_one


class RankModule:
    def __init__(self, client: discord.Client, tree: app_commands.CommandTree):
        self.client = client
        self.tree = tree

    async def setup(self) -> None:
        self._register_commands()

    def _register_commands(self) -> None:
        @self.tree.error
        async def on_command_error(
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
        ) -> None:
            if isinstance(error, app_commands.MissingPermissions):
                msg = "You need administrator permissions for that command."
            else:
                msg = "Command failed. Check logs for details."

            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

        @self.tree.command(name="rank", description="Show rank and XP for a user.")
        async def rank(
            interaction: discord.Interaction,
            user: Optional[discord.Member] = None,
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            member = user or interaction.user
            xp = self._get_user_xp(interaction.guild.id, member.id)
            rows = self._get_rank_rows(interaction.guild.id)

            current = self._highest_eligible_row(rows, xp)
            next_row = next((row for row in rows if int(row["xp"]) > xp), None)

            lines = [f"{member.mention} has **{xp} XP**."]
            if current is not None:
                role = interaction.guild.get_role(int(current["role"]))
                if role:
                    lines.append(
                        f"Current rank: {role.mention} ({int(current['xp'])} XP)"
                    )
            if next_row is not None:
                role = interaction.guild.get_role(int(next_row["role"]))
                if role:
                    remaining = max(0, int(next_row["xp"]) - xp)
                    lines.append(f"Next rank: {role.mention} in {remaining} XP")

            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @self.tree.command(name="ranks", description="List configured rank thresholds.")
        async def ranks(interaction: discord.Interaction) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            rows = self._get_rank_rows(interaction.guild.id)
            if not rows:
                await interaction.response.send_message(
                    "No ranks configured yet.", ephemeral=True
                )
                return

            lines = ["Configured ranks:"]
            for row in rows:
                role = interaction.guild.get_role(int(row["role"]))
                if role:
                    lines.append(f"- {role.mention}: {int(row['xp'])} XP")
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @self.tree.command(name="top", description="Show guild XP leaderboard.")
        async def top(
            interaction: discord.Interaction,
            limit: app_commands.Range[int, 3, 20] = 10,
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            rows = fetch_all(
                """
                SELECT user, xp
                FROM user_xp
                WHERE guild = ?
                ORDER BY xp DESC
                LIMIT ?
                """,
                (interaction.guild.id, int(limit)),
            )
            if not rows:
                await interaction.response.send_message(
                    "No XP data yet.", ephemeral=True
                )
                return

            lines = [f"Top {len(rows)} XP in {interaction.guild.name}:"]
            for i, row in enumerate(rows, start=1):
                user_id = int(row["user"])
                member = interaction.guild.get_member(user_id)
                name = member.mention if member else f"<@{user_id}>"
                lines.append(f"{i}. {name} - {int(row['xp'])} XP")

            await interaction.response.send_message("\n".join(lines))

        @self.tree.command(
            name="rankadd", description="Add or update a rank threshold."
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def rankadd(
            interaction: discord.Interaction,
            role: discord.Role,
            xp: app_commands.Range[int, 1, 100000000],
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            execute(
                """
                INSERT INTO rank_settings (guild, role, xp)
                VALUES (?, ?, ?)
                ON CONFLICT(guild, role)
                DO UPDATE SET xp = excluded.xp
                """,
                (interaction.guild.id, role.id, int(xp)),
            )
            await interaction.response.send_message(
                f"Set rank {role.mention} to {int(xp)} XP.",
                ephemeral=True,
            )

        @self.tree.command(name="rankremove", description="Remove a rank role.")
        @app_commands.checks.has_permissions(administrator=True)
        async def rankremove(
            interaction: discord.Interaction,
            role: discord.Role,
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            execute(
                "DELETE FROM rank_settings WHERE guild = ? AND role = ?",
                (interaction.guild.id, role.id),
            )
            await interaction.response.send_message(
                f"Removed rank {role.mention}.", ephemeral=True
            )

        @self.tree.command(
            name="rankchannel",
            description="Set the channel for rank change announcements.",
        )
        @app_commands.checks.has_permissions(administrator=True)
        async def rankchannel(
            interaction: discord.Interaction,
            channel: discord.TextChannel,
        ) -> None:
            if interaction.guild is None:
                await interaction.response.send_message(
                    "This command only works in a guild.", ephemeral=True
                )
                return

            execute(
                """
                INSERT INTO rank_channel (guild, rankChannel)
                VALUES (?, ?)
                ON CONFLICT(guild)
                DO UPDATE SET rankChannel = excluded.rankChannel
                """,
                (interaction.guild.id, channel.id),
            )
            await interaction.response.send_message(
                f"Rank announcements now go to {channel.mention}.",
                ephemeral=True,
            )

    def _get_rank_rows(self, guild_id: int):
        return fetch_all(
            "SELECT role, xp FROM rank_settings WHERE guild = ? ORDER BY xp ASC",
            (guild_id,),
        )

    def _get_or_create_user_row(self, guild_id: int, user_id: int):
        row = fetch_one(
            """
            SELECT guild, user, xp, minute_bucket, hour_bucket, last_message_at
            FROM user_xp
            WHERE guild = ? AND user = ?
            """,
            (guild_id, user_id),
        )
        if row:
            return row

        execute(
            """
            INSERT INTO user_xp (guild, user, xp, minute_bucket, hour_bucket, last_message_at)
            VALUES (?, ?, 0, 0, 0, 0)
            """,
            (guild_id, user_id),
        )
        return fetch_one(
            """
            SELECT guild, user, xp, minute_bucket, hour_bucket, last_message_at
            FROM user_xp
            WHERE guild = ? AND user = ?
            """,
            (guild_id, user_id),
        )

    def _get_user_xp(self, guild_id: int, user_id: int) -> int:
        row = self._get_or_create_user_row(guild_id, user_id)
        return int(row["xp"])

    def _highest_eligible_row(self, rows, xp: int):
        best = None
        for row in rows:
            if xp >= int(row["xp"]):
                best = row
            else:
                break
        return best

    def _xp_gain(
        self,
        now: float,
        last_message_at: float,
        minute_bucket: float,
        hour_bucket: float,
    ) -> tuple[int, float, float]:
        xp_cfg = config.settings.rank_xp
        dt = max(0.0, now - last_message_at)

        minute_bucket = minute_bucket * math.exp(
            -dt / xp_cfg.minute_bucket_decay_seconds
        )
        hour_bucket = hour_bucket * math.exp(-dt / xp_cfg.hour_bucket_decay_seconds)

        minute_bucket += 1.0
        hour_bucket += 1.0

        gain = int(
            round(
                xp_cfg.base_xp_gain
                + (xp_cfg.minute_activity_weight / (1.0 + minute_bucket))
                + (xp_cfg.hour_activity_weight / (1.0 + hour_bucket))
            )
        )
        gain = max(xp_cfg.min_xp_gain, min(gain, xp_cfg.max_xp_gain))
        return gain, minute_bucket, hour_bucket

    async def handle_message_xp(
        self, message: discord.Message, normalized: str
    ) -> None:
        if message.guild is None or not normalized:
            return

        guild_id = message.guild.id
        user_id = message.author.id
        now = time.time()

        row = self._get_or_create_user_row(guild_id, user_id)
        old_xp = int(row["xp"])
        gain, minute_bucket, hour_bucket = self._xp_gain(
            now,
            float(row["last_message_at"]),
            float(row["minute_bucket"]),
            float(row["hour_bucket"]),
        )
        new_xp = old_xp + gain

        execute(
            """
            UPDATE user_xp
            SET xp = ?, minute_bucket = ?, hour_bucket = ?, last_message_at = ?
            WHERE guild = ? AND user = ?
            """,
            (new_xp, minute_bucket, hour_bucket, now, guild_id, user_id),
        )

        await self._sync_member_rank(message.author, message.guild, old_xp, new_xp)

    async def _sync_member_rank(
        self,
        member: discord.Member,
        guild: discord.Guild,
        old_xp: int,
        new_xp: int,
    ) -> None:
        rows = self._get_rank_rows(guild.id)
        if not rows:
            return

        managed_ids = [int(row["role"]) for row in rows]
        target = self._highest_eligible_row(rows, new_xp)
        target_role_id = int(target["role"]) if target else None

        old_rank_id = None
        current_role_ids = {role.id for role in member.roles}
        for row in rows:
            role_id = int(row["role"])
            if role_id in current_role_ids:
                old_rank_id = role_id

        keep_roles = [role for role in member.roles if role.id not in managed_ids]
        target_role = guild.get_role(target_role_id) if target_role_id else None
        desired_roles = keep_roles + ([target_role] if target_role else [])

        before_ids = {role.id for role in member.roles}
        after_ids = {role.id for role in desired_roles if role is not None}
        if before_ids == after_ids:
            return

        try:
            await member.edit(
                roles=[role for role in desired_roles if role is not None],
                reason=f"Rank update {old_xp} XP -> {new_xp} XP",
            )
        except (discord.Forbidden, discord.HTTPException):
            return

        if old_rank_id == target_role_id or target_role is None:
            return

        dm_text = (
            f"Oi {member.display_name}, ye reached **{new_xp} XP** and now hold rank "
            f"{target_role.mention}!"
        )
        try:
            await member.send(dm_text)
        except discord.Forbidden:
            pass

        channel_row = fetch_one(
            "SELECT rankChannel FROM rank_channel WHERE guild = ?",
            (guild.id,),
        )
        if not channel_row:
            return

        channel = guild.get_channel(int(channel_row["rankChannel"]))
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(
                f"{member.mention} reached {target_role.mention} with **{new_xp} XP**!"
            )
