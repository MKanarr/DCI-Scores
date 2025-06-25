import boto3 
import requests

from boto3.dynamodb.conditions import Attr
from discord_webhook import DiscordWebhook
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# webhook
webhook = DiscordWebhook(url=getenv('HOOK_URL'))

# client
ddb = boto3.resource('dynamodb', 
                        endpoint_url='http://localhost:8000',
                        region_name='foo',
                        aws_access_key_id='foo',
                        aws_secret_access_key='foo')

# db table 
ddb_table = ddb.Table(getenv('DYNAMO_TABLE_LOCAL'))

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

def main():
    # create table
    ddb.create_table(
                        AttributeDefinitions=[
                            {
                                'AttributeName': 'ShowSlug',
                                'AttributeType': 'S'
                            }
                        ],
                        TableName='DCI-Shows-2027',
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

    ddb_table = ddb.Table('DCI-Shows-2027')

    input = [
        {
            'ShowName': 'DCI Tour Preview',
            'ShowDate': '2025-06-27',
            'ShowImageThumb': 'https://production.assets.dci.org/600x600-inset/673bb9167ac93c02e40aeb72_meF9wup6CoLxGvOpMoFx1FvdLR_swHiL.jpg',
            'ShowSlug': '2023-drums-across-the-desert',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Drums Along the Rockies',
            'ShowDate': '2025-06-28',
            'ShowImageThumb': 'https://production.assets.dci.org/600x600-inset/673bb9497ac93c02e40aeb74_WOfwkJeXxqafJCudEm-J1ElJJh1OOxo9.jpg',
            'ShowSlug': '2023-rotary-music-festival',
            'ShowRead': 'False'
        },
        {
            'ShowName': 'Barnum Festival: Champions on Parade',
            'ShowDate': '2025-06-28',
            'ShowImageThumb': 'https://production.assets.dci.org/600x600-inset/673bb95a7ac93c02e40aeb75_I1-HILf0zSg59e-Luo8Ei-s9_IpkRnW5.jpg',
            'ShowSlug': '2023-summer-music-games-in-cincinnati',
            'ShowRead': 'False'
        },
    ]

    for show_info in input:
        ddb_table.put_item(Item=show_info)

    print('Populated table')

def sort_show_scores(show_res_data, show_thumnail):

    divisions = []
    scores = []
    all_ordered_placements = []
    all_show_info = []

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
    all_show_info.append(Show(show_res_data[0]['competition']['eventName'], show_res_data[0]['competition']['date'], show_thumnail, show_res_data[0]['competition']['location'], show_res_data[0]['competition']['slug']))
    all_ordered_placements.append(ordered_placements)

    return all_show_info, all_ordered_placements

def create_embed(show_info, ordered_placements):
    field_embeds = []
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

    field_embeds.append(msg_embed)

    return field_embeds

def post_embed(msg_embed):
    for show_embed in msg_embed:
        webhook.add_embed(show_embed)

    webhook.execute()

def process_show(show_entry_data):

    slug = show_entry_data['ShowSlug']

    show_res_data = requests.get(f'{getenv("SCORE_URL")}{slug}')

    all_show_info, all_ordered_placements = sort_show_scores(show_res_data.json(), show_entry_data['ShowImageThumb'])

    field_embed = create_embed(all_show_info, all_ordered_placements)

    post_embed(field_embed)

    update_table(all_show_info)

def update_table(all_show_info):
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
    
def read_items():     
    
    entry = ddb_table.scan(
        FilterExpression=Attr('ShowDate').lte('2025-07-04') & Attr('ShowRead').eq('True')
    )

    # print(entry)

    if len(entry['Items']) == 0:
        return
    
    ### new idea

    show_items = entry['Items']

    for show_entry in show_items:
        process_show(show_entry)


    # webhook.execute()

    # return 
    ###
    
    # for item in entry['Items']:
    #     show_slugs.append(item['ShowSlug'])
    #     show_img.append(item['ShowImageThumb'])

    # for idx, slug in enumerate(show_slugs):
    #     res = requests.get(f'https://api.dci.org/api/v1/competitions/{slug}')
    
    #     if res.status_code == 200 and len(res.json()) != 0:
    #         show_res.append(res.json())

    # if len(show_res) == 0:
    #     return
    
    # for idx, specific_show in enumerate(show_res):

    #     divisons = []
    #     scores = []
        
    #     for show_details in specific_show:
    #         if show_details['divisionName'] not in divisons:
    #             divisons.append(show_details['divisionName'])
    #         scores.append(Corps(show_details['groupName'], show_details['totalScore'], show_details['divisionName'], show_details['rank']))

    #     ordered_placements = {key: [] for key in divisons}

    #     for key in ordered_placements:
    #         for corps in scores:
    #             if corps.division == key:
    #                 ordered_placements[key].append(corps)

    #         sort_scores = sorted(ordered_placements[key], key=lambda corps: corps.score, reverse=True)
    #         ordered_placements[key] = sort_scores

    #     all_show_info.append(Show(specific_show[0]['competition']['eventName'], specific_show[0]['competition']['date'], show_img[idx], specific_show[0]['competition']['location'], specific_show[0]['competition']['slug']))
    #     all_ordered_placements.append(ordered_placements)

    # for idx, show_placements in enumerate(all_ordered_placements):
    #     embed = []

    #     embed.append(
    #         {
    #             'name': 'Date',
    #             'value': all_show_info[idx].date.split('T')[0],
    #             'inline?': False
    #         }
    #     )

    #     embed.append(
    #         {
    #             'name': 'Location',
    #             'value': all_show_info[idx].location,
    #             'inline?': False
    #         }
    #     )

    #     for key, val in reversed(show_placements.items()):
    #         tmp = {
    #             'name': None,
    #             'value': None,
    #             'inline?': False,
    #         }

    #         tmp['name'] = key
    #         tmp['value'] = str(val).strip('[').strip(']').replace(',','')

    #         embed.append(tmp)

    #     embed.append(
    #         {
    #             'name': 'Recap',
    #             'value': f'https://www.dci.org/scores/recap/{all_show_info[idx].slug}'
    #         }
    #     )

    #     msg_embed = {
    #         'title': all_show_info[idx].event_name,
    #         'url': f'https://www.dci.org/scores/final-scores/{all_show_info[idx].slug}',
    #         'fields': embed,
    #         'image': {
    #             'url': f'{all_show_info[idx].image}'
    #         }
    #     }

    #     field_embeds.append(msg_embed)

    # for show_embed in field_embeds:
    #     webhook.add_embed(show_embed)

    # webhook.execute()

    # update table
    # for show in all_show_info:
    #     ddb_table.update_item(
    #         Key={
    #             'ShowSlug': show.slug,
    #         },
    #         UpdateExpression='SET ShowRead = :val1',
    #         ExpressionAttributeValues={
    #             ':val1': 'True'
    #         }
    #     )


# main()
read_items()