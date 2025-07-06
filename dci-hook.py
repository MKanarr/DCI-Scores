import boto3
import requests
import pandas as pd
import json
import pytz

from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Attr
from discord_webhook import DiscordWebhook
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass
class Corps:
    name: str
    score: float
    division: str
    rank: int

    def __str__(self):
        ranks = {
            '1': ':first_place:',
            '2': ':second_place:',
            '3': ':third_place:'
        }

        return f'{ranks.get(self.rank, self.rank)} - {self.name} - {self.score}\n'
    
def init_services():
    print("Initializing services")
    load_dotenv()
    # client
    dynamo_db = boto3.resource("dynamodb", getenv('DYNAMO_REGION'))

    return (
        DiscordWebhook(url=getenv('HOOK_URL')),
        dynamo_db.Table(getenv('DYNAMO_TABLE'))
    )

def read_items(dynamo_table): 
    print("Reading items")
    ref_date = datetime.now(pytz.timezone('America/Chicago'))
    todays_date = ref_date.strftime('%Y-%m-%d')
    preivous_date = (ref_date - timedelta(1)).strftime('%Y-%m-%d')
    print(todays_date)
    print(preivous_date)

    return dynamo_table.scan(
        FilterExpression=Attr("ShowRead").eq("False") & Attr("ShowDate").between(preivous_date, todays_date)
    )

def update_table(show_items, processed_slugs, dynamo_table):
    print("Updating table")
    print(processed_slugs)
    for show_item in show_items:
        if show_item['ShowSlug'] in processed_slugs:
            print("Marking as read: ", show_item['ShowSlug'])
            dynamo_table.update_item(
                Key={
                    'ShowSlug': show_item['ShowSlug'],
                },
                UpdateExpression='SET ShowRead = :val1',
                ExpressionAttributeValues={
                    ':val1': 'True'
                }
            )

def post_embed(webhook, msg_embed):
    print("Posting embed")
    for show_embed in msg_embed:
        webhook.add_embed(show_embed)

    webhook.execute(remove_embeds=True)
    
def create_embed(show_df, slug, show_img, show_name, show_date):
    print("Creating embed")
    show_location = show_df["Location"].unique()[0]
    embed_fields = [
        {
            'name': 'Location',
            'value': show_location,
            'inline?': False
        },
        {
            'name': 'Date',
            'value': show_date,
            'inline?': False
        }
    ]

    # Group corps by division
    divisions = show_df["Division"].unique()
    for division in divisions:
        corps_rows = show_df[show_df["Division"] == division]
        corps_entries = [
            Corps(
                row["Corps"],
                row["Score"],
                row["Division"],
                row["Place"]
            )
            for _, row in corps_rows.iterrows()
        ]
        embed_fields.append({
            "name": division,
            "value": "".join(str(c) for c in corps_entries),
            "inline?": False,
        })

    embed_fields.append({
        "name": "Recap",
        "value": f"https://www.dci.org/scores/recap/{slug}",
    })

    return {
        "title": show_name,
        "url": f"https://www.dci.org/scores/final-scores/{slug}",
        "fields": embed_fields,
        "image": {"url": show_img},
    }

def process_show(show_entry_data):
    print("Processing show: ", show_entry_data['ShowSlug'])
    slug = show_entry_data['ShowSlug']
    img = show_entry_data['ShowImageThumb']
    name = show_entry_data['ShowName']
    date = show_entry_data['ShowDate']

    header = {
        'User-Agent' : (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"   
        )
    }

    url = f"{getenv("SCORE_URL")}{slug}"

    ### webscrape
    try:
        dci_score_page = requests.get(url, headers=header)
        dci_score_page.raise_for_status()
        show_df = parse_html(dci_score_page)
        return create_embed(show_df, slug, img, name, date)
    except (requests.RequestException, ValueError) as e:
        print(f'Error processing show {slug}: {e}')
        return None
    
def parse_html(html_page):
    print("Parsing HTML")
    soup = BeautifulSoup(html_page.content, 'html.parser')
    score_location = soup.find("div", class_="score-date-location")
    main_table = soup.find("div", class_="finalscores")
    children = list(main_table.children)
    all_rows = []

    j = 0

    while j < len(list(score_location.children)):
        child = list(score_location.children)[j]
        if child.name == "p" and j == 3:
            show_location = child.get_text(strip=True)
        j += 1

    i = 0

    while i < len(children):
        child = children[i]
        
        if child.name == "div":
            h2 = child.find("h2", class_="score-division-name")
            if h2:
                division_name = h2.get_text(strip=True)
                # Skip the header row div
                i += 2
                # Now loop over tbl-rows until next division heading or end
                while i < len(children):
                    row_div = children[i]
                    if row_div.name == "div":
                        # Check if this is a new division heading
                        h2_new = row_div.find("h2", class_="score-division-name")
                        if h2_new:
                            break  # Done with current division
                        # Process tbl-row (skip poweredby)
                        if "tbl-row" in row_div.get("class", []) and "poweredby-row" not in row_div.get("class", []):
                            row = row_div.find("div", class_="row")
                            place = row.find("div", class_="col-2").get_text(strip=True)
                            corps = row.find("div", class_="col-7").get_text(strip=True)
                            score = row.find("div", class_="col-3").get_text(strip=True)
                            all_rows.append({
                                "Division": division_name,
                                "Place": place,
                                "Corps": corps,
                                "Score": score,
                                "Location": show_location
                            })
                    i += 1
        else:
            i += 1

    print(all_rows)

    return pd.DataFrame(all_rows)
            
def lambda_handler(event, context):
    print("Invoking Lambda")
    field_embeds = []
    processed_slugs = []
    webhook, dynamo_table = init_services()
    db_entry = read_items(dynamo_table)

    if len(db_entry['Items']) == 0:
        return
    
    show_items = db_entry['Items']

    print(show_items)

    for show_entry in show_items:
        try:
            embed = process_show(show_entry)
            if embed:
                field_embeds.append(embed)
                processed_slugs.append(show_entry['ShowSlug'])
        except Exception as e: 
            print(f'Error processing show {show_entry["ShowSlug"]}: {e}')
            continue

    if field_embeds:
        print("All shows processed successfully.")
        post_embed(webhook, field_embeds)
        update_table(show_items, processed_slugs, dynamo_table)
        return {
            'statusCode': 200,
            'body': json.dumps('Posted Scores')
        }
    else:
        print("All shows failed to process or no embeds created.")
        return {
            'statusCode': 200,
            'body': json.dumps('No shows processed successfully')
        }