import json
import discord
import aiohttp
import operator
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv

load_dotenv()

bot = commands.Bot(command_prefix='.')

@bot.command()
async def scores(ctx):
    comp_url = getenv('COMP_URL')
    score_url = getenv('SCORE_URL')

    async with aiohttp.ClientSession() as session:
        async with session.get(comp_url) as response:
            if response.status == 200:
                comp_res = await response.json()
        
        show_slug = comp_res[0]['slug']
        show_name = comp_res[0]['eventName'] 
        show_location = comp_res[0]['location']

        async with session.get(score_url + show_slug) as response:
            if response.status == 200:
                show_res = await response.json()

        world_c = {}
        open_c = {}

        for show_info in show_res:
            if show_info['divisionName'] == 'World Class':
                world_c[show_info['groupName']] = show_info['totalScore']
            else:
                open_c[show_info['groupName']] = show_info['totalScore']

        world_c_sort = sorted(world_c.items(), key=operator.itemgetter(1), reverse=True)
        open_c_sort = sorted(open_c.items(), key=operator.itemgetter(1), reverse=True)

        world_c_str = '\n'.join(map(str, world_c_sort)).replace("(","").replace(")","")
        open_c_str = '\n'.join(map(str, open_c_sort)).replace("(","").replace(")","")

        emb = discord.Embed(title=show_name, url=f"https://www.dci.org/scores/final-scores/{show_slug}")
        emb.description = show_location
        emb.add_field(name="World Class", value=world_c_str, inline=False)
        emb.add_field(name="Open Class", value=open_c_str, inline=False)
        emb.add_field(name="Recap", value=f"https://www.dci.org/scores/recap/{show_slug}", inline=False)

        await ctx.send(embed=emb)


bot.run(getenv('BOT_TOKEN'))
