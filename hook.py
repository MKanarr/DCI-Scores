import discord
import requests

hook_url = f'https://discord.com/api/webhooks/1125909458015490148/jPDvMFHhDsALHqFZtOiPTUiEtud8zUZVf7riAkOPq_l6rBfr3i_KMRgXNwlvCND14L1a'

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