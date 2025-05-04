import json
import requests
import urllib.parse

from .preferences import SETTINGS

def get_count(query):
    try:
        response = requests.get("https://danbooru.donmai.us/counts/posts.json", params=filter_query(query))
        return response.json()["counts"]["posts"]
    except:
        return None

def get_catalog(query, page=1):
    params = f"{filter_query(query)}&page={page}&limit={SETTINGS.get_int('posts-per-page')}"
    try:
        response = requests.get("https://danbooru.donmai.us/posts.json", params=params)
        return [i for i in response.json() if "file_url" in i and not i["file_url"].endswith("swf")]
    except:
        return None

def get_post(id):
    try:
        response = requests.get(f"https://danbooru.donmai.us/posts/{id}.json")
        return response.json()
    except:
        return None

def filter_query(query):
    if SETTINGS.get_boolean("safe-mode"):
        query += " rating:g,s"
    if not SETTINGS.get_boolean("pending-posts"):
        query += " status:active"
    if SETTINGS.get_boolean("deleted-posts") and SETTINGS.get_boolean("pending-posts"):
        query += " status:any"
    return f"tags={urllib.parse.quote(query)}"

def get_content(url):
    try:
        response = requests.get(url)
        return response.content
    except:
        return None
