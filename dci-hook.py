import boto3
import requests

from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from discord_webhook import DiscordWebhook

load_dotenv()

# webhook
webhook = DiscordWebhook(url=getenv('HOOK_URL'))
current_date = datetime.today().strftime('%Y-%m-%d')
# client
dynamo_db = boto3.resource("dynamodb", getenv('AWS_REGION'))
# db table
dynamo_table = dynamo_db.Table(getenv('DYNAMO_TABLE'))

class Show:
    def __init__(self, event_name, date, image, location, slug):
        self.event_name = event_name
        self.date = date
        self.image = image
        self.location = location
        self.slug = slug

    def __str__(self):
        return f'{self.event_name} - {self.date} - {self.image} - {self.location} - {self.slug}'

    def __repr__(self):
        return str(self)

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
    
def sort_show_scores(show_res_data, show_thumnail):

    divisions = []
    scores = []
    all_ordered_placements = []
    all_show_info = []

    event_name = show_res_data[0]['competition']['eventName']
    event_date = show_res_data[0]['competition']['date']
    event_location = show_res_data[0]['competition']['location']
    show_slug = show_res_data[0]['competition']['slug']

    # populate show score data from api response
    for show_details in show_res_data:
        # populate divisions present at show - world, open, etc.
        if show_details['divisionName'] not in divisions:
            divisions.append(show_details['divisionName'])
        scores.append(Corps(show_details['groupName'], show_details['totalScore'], show_details['divisionName'], show_details['rank']))

    ordered_placements = {key: [] for key in divisions}

    # sort placements based on scores and group by division
    for key in ordered_placements:
        for corps in scores:
            if corps.division == key:
                ordered_placements[key].append(corps)

        sort_scores = sorted(ordered_placements[key], key=lambda corps: corps.score, reverse=True)
        ordered_placements[key] = sort_scores

    # show information
    all_show_info.append(Show(event_name, event_date, show_thumnail, event_location, show_slug))
    all_ordered_placements.append(ordered_placements)

    return all_show_info, all_ordered_placements

def create_embed(show_info, ordered_placements):
    embed = []
    show_name = show_info[0].event_name
    show_date = show_info[0].date.split('T')[0]
    show_location = show_info[0].location
    show_slug = show_info[0].slug
    show_image = show_info[0].image

    embed.append(
        {
            'name': 'Date',
            'value': show_date,
            'inline?': False
        }
    )

    embed.append(
        {
            'name': 'Location',
            'value': show_location,
            'inline?': False
        }
    )

    for key, val in reversed((ordered_placements[0]).items()):
        tmp = {
            'name': None,
            'value': None,
            'inline?': False,
        }

        tmp['name'] = key
        tmp['value'] = str(val).strip('[').strip(']').replace(',','')

        embed.append(tmp)

    embed.append(
        {
            'name': 'Recap',
            'value': f'https://www.dci.org/scores/recap/{show_slug}'
        }
    )

    msg_embed = {
        'title': show_name,
        'url': f'https://www.dci.org/scores/final-scores/{show_slug}',
        'fields': embed,
        'image': {
            'url': f'{show_image}'
        }
    }

    return msg_embed

def post_embed(msg_embed):
    for show_embed in msg_embed:
        webhook.add_embed(show_embed)

    webhook.execute()

def process_show(show_entry_data):

    slug = show_entry_data['ShowSlug']

    show_res_data = requests.get(f'{getenv("SCORE_URL")}{slug}')

    if show_res_data.status_code != 200 and len(show_res_data.json()) == 0:
        return

    all_show_info, all_ordered_placements = sort_show_scores(show_res_data.json(), show_entry_data['ShowImageThumb'])

    return create_embed(all_show_info, all_ordered_placements)

def update_table(show_items):
    for show_item in show_items:
        dynamo_table.update_item(
            Key={
                'ShowSlug': show_item['ShowSlug'],
            },
            UpdateExpression='SET ShowRead = :val1',
            ExpressionAttributeValues={
                ':val1': 'True'
            }
        )
    
def read_items():     
    entry = dynamo_table.scan(
        FilterExpression=Attr('ShowDate').lte(current_date) & Attr('ShowRead').eq('False')
    )
    
    return entry
    
def lambda_handler(event, context):
    field_embeds = []
    db_entry = read_items()

    if len(db_entry['Items']) == 0:
        return
    
    show_items = db_entry['Items']

    for show_entry in show_items:
        field_embeds.append(process_show(show_entry))

    post_embed(field_embeds)

    update_table(show_items)