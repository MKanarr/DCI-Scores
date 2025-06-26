import boto3
import requests

from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from discord_webhook import DiscordWebhook
from dataclasses import dataclass

@dataclass
class Show:
    event_name: str
    date: str
    image: str
    location: str
    slug: str

    def __str__(self):
        return f'{self.event_name} - {self.date} - {self.image} - {self.location} - {self.slug}'

@dataclass
class Corps:
    name: str
    score: float
    division: str
    rank: int

    def __str__(self):
        return f'{self.rank} - {self.name} - {self.score}\n'
    
def init_services():
    load_dotenv()
    # webhook
    webhook = DiscordWebhook(url=getenv('HOOK_URL'))
    # client
    dynamo_db = boto3.resource("dynamodb", getenv('DYNAMO_REGION'))
    # db table
    dynamo_table = dynamo_db.Table(getenv('DYNAMO_TABLE'))
    return webhook, dynamo_table

def read_items(dynamo_table): 
    current_date = datetime.today().strftime('%Y-%m-%d')    
    entry = dynamo_table.scan(
        FilterExpression=Attr('ShowDate').lte(current_date) & Attr('ShowRead').eq('False')
    )
    
    return entry

def post_embed(webhook, msg_embed):
    for show_embed in msg_embed:
        webhook.add_embed(show_embed)

    webhook.execute(remove_embeds=True)

def update_table(show_items, dynamo_table):
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
    show = show_info[0]

    embed_fields = [
        {
            'name': 'Date',
            'value': show.date.split('T')[0],
            'inline?': False
        },
        {
            'name': 'Location',
            'value': show.location,
            'inline?': False
        }
    ]

    for division, corps_list in reversed((ordered_placements[0]).items()):
        embed_fields.append(
            {
                'name': division,
                'value': ''.join(str(c) for c in corps_list),
                'inline?': False,
            }
        )

    embed_fields.append(
        {
            'name': 'Recap',
            'value': f'https://www.dci.org/scores/recap/{show.slug}'
        }
    )

    msg_embed = {
        'title': show.event_name,
        'url': f'https://www.dci.org/scores/final-scores/{show.slug}',
        'fields': embed_fields,
        'image': {
            'url': f'{show.image}'
        }
    }

    return msg_embed

def process_show(show_entry_data):
    slug = show_entry_data['ShowSlug']

    try:
        show_res_data = requests.get(f'{getenv("SCORE_URL")}{slug}')
        show_res_data.raise_for_status()
        show_data = show_res_data.json()
        all_show_info, all_ordered_placements = sort_show_scores(show_data, show_entry_data['ShowImageThumb'])
        return create_embed(all_show_info, all_ordered_placements)
    except (requests.RequestException, ValueError) as e:
        print(f'Error processing show {slug}: {e}')
        return None
            
def lambda_handler(event, context):
    field_embeds = []
    webhook, dynamo_table = init_services()
    db_entry = read_items(dynamo_table)

    if len(db_entry['Items']) == 0:
        return
    
    show_items = db_entry['Items']

    for show_entry in show_items:
        embed = process_show(show_entry)
        if embed:
            field_embeds.append(embed)

    post_embed(webhook, field_embeds)

    update_table(show_items, dynamo_table)