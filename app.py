import os
import json
import ssl

import requests 
from slack_sdk import WebClient
from bs4 import BeautifulSoup as bs 
from datetime import date

# Deactivate SSL for Slack Client
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

BLOG_URL = "https://blog.alvinend.tech"
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

def lambda_handler(event, context):
    # Get Website HTML 
    r = requests.get(BLOG_URL) 

    # Covert to BeautifulSoup 
    soup = bs(r.content)

    # Get Page Posts Metadata
    target = soup.find('script', {'id': '__NEXT_DATA__'}).text
    json_target = json.loads(target)
    hashnode_posts = json.loads(json_target['props']['pageProps']['posts'])

    # Pull last data from S3

    # Loop Post and Extract Useful Property
    posts = []
    for post in hashnode_posts:
        posts.append({
            "title": post["title"],
            "views": post['views'],
            "replyCount": post["replyCount"],
            "reactionCount": len(post['reactions'])
        })

    # Save Data to S3
    print(posts)
    
    # Init Slack Client
    client = WebClient(token=SLACK_BOT_TOKEN, ssl=ssl_context)

    today = date.today()
    text =f"*【{today.strftime('%Y/%m/%d')}】blog.alvinend.tech Blog Statistic*\n"

    for post in posts:
        text += "================================================================ \n"
        text += f"*{post['title']}* \n"
        text += f"Views: {post['views']} *(+0)* \n"
        text += f"Reply Count: {post['replyCount']} *(+0)* \n"
        text += f"Reaction Count: {post['reactionCount']} *(+0)* \n"
        text += "\n"

        
    # Send Message to Slack
    client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=text)

