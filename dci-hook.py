import boto3
import requests

from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from boto3.dynamodb.conditions import Attr

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

def lambda_handler(event, context):

    # dynamo_db = boto3.resource("dynamodb", getenv('AWS_REGION'))
    # dynamo_table = dynamo_db.Table(getenv('DYNAMO_TABLE'))
    # add condition to only pick entries with false show read
    # entry = dynamo_table.scan(
    #     FilterExpression=Attr("ShowDate").eq("2023-07-03") & Attr("ShowRead").eq("False")
    # )

    # if len(entry["Items"]) == 0:
    #     return

    show_names = []
    show_slugs = []
    show_scores = []

    for item in event["Items"]:
        print(item)
        show_names.append(item["ShowName"])
        # should already know date in advance will pass as param into scan
        show_slugs.append(item["ShowSlug"])

    for slug in show_slugs:
        # make api call
        response = requests.get(f'{getenv("SCORE_URL")}{slug}')
        # do operations / sorting for that show
        if response.status_code == 200 and len(response.json()) != 0: 
            show_scores.append(response.json())

    # print(show_scores)
    # print(len(show_scores))

    divisions = []

    for show in show_scores:
        print(show)

if __name__ == "__main__":
    event = {
        "Items": [
            {
                "ShowName": "Drums Across the Desert",
                "ShowDate": "2023-07-03",
                "ShowSlug": "2023-drums-across-the-desert",
                "ShowRead": "False"
            },
            {
                "ShowName": "Rotary Music Festival",
                "ShowDate": "2023-07-03",
                "ShowSlug": "2023-rotary-music-festival",
                "ShowRead": "False"
            }    
        ]
    }
    lambda_handler(event, None)