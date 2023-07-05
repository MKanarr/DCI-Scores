import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from datetime import datetime

load_dotenv()

class Corps:
    def __init__(self, name, score, division, rank):
        self.name = name
        self.score = score
        self.division = division
        self.rank = rank

    def __str__(self):
        return f'{self.rank} - {self.name} - {self.score}\n'

    def __repr__(self):
        return str(self)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

year = str(datetime.now().year)

@bot.command()
async def scores(ctx):
    show_url = getenv('SHOW_URL')
    score_url = getenv('SCORE_URL')

    async with aiohttp.ClientSession() as session:
        async with session.get(show_url + year) as response:
            if response.status == 200:
                show_info = await response.json()
        
        show_date = show_info[0]['date']
        show_slug = show_info[0]['slug']
        show_name = show_info[0]['eventName'] 
        show_location = show_info[0]['location']

        async with session.get(f'{score_url}{show_slug}') as response:
            if response.status == 200:
                score_info = await response.json()

        scores = []
        divisions = []

        for field in score_info:
            if field['divisionName'] not in divisions:
                divisions.append(field['divisionName'])
            scores.append(Corps(field['groupName'], field['totalScore'], field['divisionName'], field['rank']))

        ordered_placements = {key: [] for key in divisions}

        for key in ordered_placements:
            for corps in scores:
                if corps.division == key:
                    ordered_placements[key].append(corps)

            sort_scores = sorted(ordered_placements[key], key=lambda corps: corps.score, reverse=True)
            ordered_placements[key] = sort_scores

        field_embed = []

        fixed_date = show_date.split('T')[0]

        field_embed.append(
            {
                'name': 'Date',
                'value': fixed_date,
                'inline?': False,
            }
        )        

        field_embed.append(
            {
                'name': 'Location',
                'value': show_location,
                'inline?': False,
            }
        )    

        for key, val in ordered_placements.items():
            tmp = {
                'name': None,
                'value': None,
                'inline?': False,
            }

            tmp['name'] = key
            tmp['value'] = str(val).strip('[').strip(']').replace(',','')

            field_embed.append(tmp)

        field_embed.append(
            {
                'name': 'Recap',
                'value': f'https://www.dci.org/scores/recap/{show_slug}',
                'inline?': False,
            }
        )

        msg_embed = {
            'title': show_name,
            'url': f'https://www.dci.org/scores/final-scores/{show_slug}',
            'fields': field_embed,
        }

        emb = discord.Embed.from_dict(msg_embed)
         
        await ctx.send(embed=emb)


bot.run(getenv('BOT_TOKEN'))
