import requests

api_url = "http://snoweagle.tk/chat/"


def hagrid(query):
    response = requests.get(
        api_url,
        {
            "prompt": f"This is a conversation between a user and the loyal, friendly, and softhearted Rubeus Hagrid with a thick west country accent.\nUser: {query}\nHagrid:",
            "player": "User",
            "villager": "Hagrid",
        },
        timeout=5.0,
    )

    return response.json()["answer"].strip()
