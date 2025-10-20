from typing import List

import requests

api_url = "https://mca.conczin.net/v1/user/mca/"
ENABLED = True


def escape_markdown(t):
    return t.replace("_", " ").replace("  ", " ").strip()


def library():
    if not ENABLED:
        return "Whoops, that's not available right now. Try again later!"

    response: List = requests.get(
        api_url,
        timeout=5.0,
    ).json()["users"]

    most_likes = sorted(response, key=lambda v: v["likes_received"], reverse=True)[:3]
    most_submissions = sorted(
        response, key=lambda v: v["submission_count"], reverse=True
    )[:3]

    return "\n".join(
        [
            "Well, blimey! Look who we've got 'ere! Our top content creators fer the skin library:",
            "```md",
            f"1. {escape_markdown(most_likes[0]['username'])} with {most_likes[0]['likes_received']} likes",
            f"2. {escape_markdown(most_likes[1]['username'])} with {most_likes[1]['likes_received']} likes",
            f"3. {escape_markdown(most_likes[2]['username'])} with {most_likes[2]['likes_received']} likes",
            "```",
            "```md",
            f"1. {escape_markdown(most_submissions[0]['username'])} with {most_submissions[0]['submission_count']} submissions",
            f"2. {escape_markdown(most_submissions[1]['username'])} with {most_submissions[1]['submission_count']} submissions",
            f"3. {escape_markdown(most_submissions[2]['username'])} with {most_submissions[2]['submission_count']} submissions",
            "```",
        ]
    )
