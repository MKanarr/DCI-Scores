import boto3 
import requests

from boto3.dynamodb.conditions import Attr
from discord_webhook import DiscordWebhook

# webhook
webhook = DiscordWebhook(url=f'https://discord.com/api/webhooks/1126018605293785108/22d15cloTS0uQUSokdlX4YGVh1DhJUf31mMviyl0oVgpXlzjWwc2QCB-n7Py8qCTrsvN')

# client
ddb = boto3.resource('dynamodb', 
                        endpoint_url='http://localhost:8000',
                        region_name='foo',
                        aws_access_key_id='foo',
                        aws_secret_access_key='foo')


class Show:
    def __init__(self, event_name, date, location, slug):
        self.event_name = event_name
        self.date = date
        self.location = location
        self.slug = slug

    def __str__(self):
        return f'{self.event_name}'

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

def main():
    # create table
    ddb.create_table(
                        AttributeDefinitions=[
                            {
                                'AttributeName': 'ShowSlug',
                                'AttributeType': 'S'
                            }
                        ],
                        TableName='DCI-Shows-2023',
                        KeySchema=[
                            {
                                'AttributeName': 'ShowSlug',
                                'KeyType': 'HASH'
                            }
                        ],
                        ProvisionedThroughput= {
                                'ReadCapacityUnits': 10,
                                'WriteCapacityUnits': 10
                        }
                    )
    
    print('CreatedTable')

    ddb_table = ddb.Table('DCI-Shows-2023')

    input = [
        {
            'ShowName': 'Drums Across the Desert',
            'ShowDate': '2023-07-03',
            'ShowSlug': '2023-drums-across-the-desert',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Rotary Music Festival',
            'ShowDate': '2023-07-03',
            'ShowSlug': '2023-rotary-music-festival',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Summer Music Games in Cincinnati',
            'ShowDate': '2023-07-05',
            'ShowSlug': '2023-summer-music-games-in-cincinnati',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'MidCal Champions Showcase',
            'ShowDate': '2023-07-07',
            'ShowSlug': '2023-midcal-champions-showcase',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'CrownBEAT',
            'ShowDate': '2023-07-08',
            'ShowSlug': '2023-crownbeat',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Drum Corps at the Rose Bowl',
            'ShowDate': '2023-07-08',
            'ShowSlug': '2023-drum-corps-at-the-rose-bowl',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Whitewater Classic',
            'ShowDate': '2023-07-08',
            'ShowSlug': '2023-whitewater-classic',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'DCI Macon',
            'ShowDate': '2023-07-09',
            'ShowSlug': '2023-dci-macon',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'DCI West',
            'ShowDate': '2023-07-09',
            'ShowSlug': '2023-dci-west',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'River City Rhapsody - La Crosse',
            'ShowDate': '2023-07-09',
            'ShowSlug': '2023-river-city-rhapsody-la-crosse',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'DCI Capital Classic',
            'ShowDate': '2023-07-10',
            'ShowSlug': '2023-dci-capital-classic',
            'ShowRead': 'False'
        }
    ]

    for show_info in input:
        ddb_table.put_item(Item=show_info)

    print('Populated table')

def read_items(): 
    
    show_slugs = []
    show_res = []
    all_ordered_placements = []
    all_show_info = []
    field_embeds = []
    
    ddb_table = ddb.Table('DCI-Shows-2023')

    entry = ddb_table.scan(
        FilterExpression=Attr('ShowDate').lte('2023-07-04') & Attr('ShowRead').eq('False')
    )

    if len(entry['Items']) == 0:
        return
    
    for item in entry['Items']:
        show_slugs.append(item['ShowSlug'])

    for idx, slug in enumerate(show_slugs):
        res = requests.get(f'https://api.dci.org/api/v1/competitions/{slug}')
    
        if res.status_code == 200 and len(res.json()) != 0:
            show_res.append(res.json())

    if len(show_res) == 0:
        return
    
    for idx, specific_show in enumerate(show_res):

        divisons = []
        scores = []
        
        for show_details in specific_show:
            if show_details['divisionName'] not in divisons:
                divisons.append(show_details['divisionName'])
            scores.append(Corps(show_details['groupName'], show_details['totalScore'], show_details['divisionName'], show_details['rank']))

        ordered_placements = {key: [] for key in divisons}

        for key in ordered_placements:
            for corps in scores:
                if corps.division == key:
                    ordered_placements[key].append(corps)

            sort_scores = sorted(ordered_placements[key], key=lambda corps: corps.score, reverse=True)
            ordered_placements[key] = sort_scores
        
        all_show_info.append(Show(specific_show[0]['competition']['eventName'], specific_show[0]['competition']['date'], specific_show[0]['competition']['location'], specific_show[0]['competition']['slug']))
        all_ordered_placements.append(ordered_placements)

    for idx, show_placements in enumerate(all_ordered_placements):
        embed = []

        embed.append(
            {
                'name': 'Date',
                'value': all_show_info[idx].date.split('T')[0],
                'inline?': False
            }
        )

        embed.append(
            {
                'name': 'Location',
                'value': all_show_info[idx].location,
                'inline?': False
            }
        )

        for key, val in reversed(show_placements.items()):
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
                'value': f'https://www.dci.org/scores/recap/{all_show_info[idx].slug}'
            }
        )

        msg_embed = {
            'title': all_show_info[idx].event_name,
            'url': f'https://www.dci.org/scores/final-scores/{all_show_info[idx].slug}',
            'fields': embed,
            'image': {
                'url': f'https://production.assets.dci.org/6383b1af002bc235950f5eb9_Cf1DVvPNj8pv8jCdNANPn2Law7v3mKGl.jpeg'
            }
        }

        field_embeds.append(msg_embed)

    for show_embed in field_embeds:
        webhook.add_embed(show_embed)

    webhook.execute()

    # update table
    for show in all_show_info:
        ddb_table.update_item(
            Key={
                'ShowSlug': show.slug,
            },
            UpdateExpression='SET ShowRead = :val1',
            ExpressionAttributeValues={
                ':val1': 'True'
            }
        )


main()
read_items()