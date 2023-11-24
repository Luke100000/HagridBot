import re

from difflib import SequenceMatcher


def load():
    c = []
    with open("minecraft-comes-alive.wiki/Config.md", "r") as file:
        comment = []
        config = []
        name = None
        for line in file:
            line = line
            if line.startswith("//"):
                # start of comment
                comment.append(line.strip())
            elif line.startswith('"'):
                # if the last config didn't finished, let's share the comments
                if name is not None:
                    c.append((name, "\n".join(comment), "\n".join(config)))
                    config = []

                # start of config
                name = line[1 : line.find('"', 1)]
                config.append(re.sub(r"[\n\r]+", "", line))
            elif (len(line.strip()) == 0 or line == "```") and name is not None:
                # end of config
                c.append((name, "\n".join(comment), "\n".join(config)))
                name = None
                config = []
                comment = []
            else:
                config.append(re.sub(r"[\n\r]+", "", line))
    return c


configs = load()


def retrieve(query):
    results = []
    for name, comment, config in configs:
        matches = 0
        for word in re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower().split():
            for search in query.lower().split():
                sim = SequenceMatcher(None, word, re.sub(r"\W+", "", search)).ratio()
                if sim > 0.75:
                    matches += 1

        if matches > 0:
            results.append(
                (
                    matches,
                    "```java\n" + (comment + "\n" + config) + "\n```",
                )
            )

    if len(results) == 0:
        return "Didn't find anythin'."

    results = sorted(results, key=lambda v: v[0], reverse=True)

    max_prints = 5

    return "\n".join([r[1] for r in results][:max_prints]) + (
        ""
        if len(results) <= max_prints
        else f"\nAn {len(results) - max_prints} more."
    )
