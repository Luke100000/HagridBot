import os
import shelve

os.makedirs("shelve/", exist_ok=True)
stats = shelve.open("shelve/stats")


def stat(message, typ):
    guild = message.guild.name
    if guild in stats:
        g: dict = stats[guild]
        if typ in g:
            g[typ] += 1
        else:
            g[typ] = 1
        stats[guild] = g
    else:
        stats[guild] = {typ: 1}
    stats.sync()
