import discord
import requests

from dotenv import load_dotenv
from os import getenv

hook_url = getenv('TEST_HOOK_URL')

msg = {
    "embeds": [
        {
            'title': 'Some DCI Show',
            'url': f'https://www.dci.org/scores/final-scores/',
            'image': {
                'url': f'https://production.assets.dci.org/6383b1af002bc235950f5eb9_Cf1DVvPNj8pv8jCdNANPn2Law7v3mKGl.jpeg'
            }        
        }
    ]
}

msg_embed = {
    'title': 'Some DCI Show',
    'url': f'https://www.dci.org/scores/final-scores/'
}

requests.post(hook_url, json=msg)