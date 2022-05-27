import os
import json
import ssl

import requests 
from slack_sdk import WebClient
from bs4 import BeautifulSoup as bs 
from datetime import date
import time

# Deactivate SSL for Slack Client
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

BLOG_URL = "https://blog.alvinend.tech"
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

def lambda_handler(event, context):
    # Hourly Report Here
    report_today_weather()

    current_gmt_hour = time.gmtime(time.time()).tm_hour
    # Daily Report Here
    if  current_gmt_hour != 20:
        return None

    report_blog_stats()


def report_today_weather():
    try:
        # Get Website HTML 
        r = requests.get("http://api.weatherapi.com/v1/forecast.json?key=82ee8a5af9dd4ff585090337222705&q=35.0142,135.7482&days=1&aqi=no&alerts=yes") 

        forecast_weather = r.json()['forecast']['forecastday'][0]
        day_forecast_weather = r.json()['forecast']['forecastday'][0]['day']

        channel_id = "C03H61BEVKP" # Weather Channe;

        client = WebClient(token=SLACK_BOT_TOKEN, ssl=ssl_context)

        # Image
        img_url = "https://images.unsplash.com/photo-1546587348-d12660c30c50?ixlib=rb-1.2.1&dl=clement-fusil-Fpqx6GGXfXs-unsplash.jpg&w=640&q=80&fm=jpg&crop=entropy&cs=tinysrgb"
        if day_forecast_weather["daily_will_it_rain"] == 1:
            img_url = "https://images.unsplash.com/photo-1517398629-9d24ea1f4f94?ixlib=rb-1.2.1&dl=craig-whitehead-y9uWW3uZ-bk-unsplash.jpg&w=640&q=80&fm=jpg&crop=entropy&cs=tinysrgb"

        if day_forecast_weather["daily_will_it_snow"] == 1:
            img_url = "https://images.unsplash.com/photo-1517166357932-d20495eeffd7?ixlib=rb-1.2.1&dl=joy-real-yVN_pjkCc3I-unsplash.jpg&w=640&q=80&fm=jpg&crop=entropy&cs=tinysrgb"

        # Chance
        pour_chance = day_forecast_weather['daily_chance_of_rain']

        if day_forecast_weather['daily_chance_of_rain'] < day_forecast_weather['daily_chance_of_snow']:
            pour_chance = day_forecast_weather['daily_chance_of_snow']


        client.chat_postMessage(
            channel=channel_id,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{forecast_weather['date']} Weather*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"Temperature: {day_forecast_weather['maxtemp_c']}°C ~ {day_forecast_weather['mintemp_c']}°C (Avg: {day_forecast_weather['avgtemp_c']}°C) \n"
                            f"Precipitation: {pour_chance}% \n \n"
                            f"*{day_forecast_weather['condition']['text']}*"
                        )
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": img_url,
                        "alt_text": "Weather"
                    }
                }
            ]
        )
    except Exception as e:
        print(e)
        client.chat_postMessage(channel=channel_id, text=f"Error: {repr(e)}")

def report_blog_stats():
    try:
        channel_id = "C03H47ZC6VA" # blogs

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
        client.chat_postMessage(channel=channel_id, text=text)
    except Exception as e:
        print(e)
        client.chat_postMessage(channel=channel_id, text=f"Error: {repr(e)}")