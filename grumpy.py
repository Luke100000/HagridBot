import requests

api_url = "http://snoweagle.tk/chat/"


def grumpy(query):
    response = requests.get(
        api_url,
        {
            "prompt": f"This is a conversation between a user and a very grumpy Rubeus Hagrid with a thick west country accent.\nUser: {query}\nHagrid:",
            "player": "User",
            "villager": "Hagrid",
        },
    )

    return response.json()["answer"].strip()
