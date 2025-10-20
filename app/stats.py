import shelve

from app.config import get_data_path

stats = shelve.open(get_data_path("stats"))


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
