import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET

BASE_URL = 'https://cfts.org.ua'

def get_articles(section_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(section_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = []
    now = datetime.datetime.now()

    for block in soup.select('div.news_block'):
        title_tag = block.select_one('div.news_title > a')
        date_tag = block.select_one('div.news_date')

        if not title_tag or not date_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = BASE_URL + title_tag['href']
        try:
            pub_date = datetime.datetime.strptime(date_tag.text.strip(), '%d.%m.%Y %H:%M')
        except ValueError:
            continue

        if now - pub_date <= datetime.timedelta(days=30):
            articles.append({'title': title, 'link': link, 'pub_date': pub_date})

    return articles

def generate_rss(articles, filename):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')

    ET.SubElement(channel, 'title').text = 'CFTS.org.ua — Новости, Статьи, Аналитика'
    ET.SubElement(channel, 'link').text = BASE_URL
    ET.SubElement(channel, 'description').text = 'Последние новости, статьи и аналитика'
    ET.SubElement(channel, 'language').text = 'ru'

    for article in sorted(articles, key=lambda x: x['pub_date'], reverse=True):
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = article['title']
        ET.SubElement(item, 'link').text = article['link']
        ET.SubElement(item, 'pubDate').text = article['pub_date'].strftime('%a, %d %b %Y %H:%M:%S +0000')

    tree = ET.ElementTree(rss)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

def main():
    sections = [
        'https://cfts.org.ua/news/',
        'https://cfts.org.ua/articles/',
        'https://cfts.org.ua/analytics/',
    ]

    all_articles = []
    for url in sections:
        all_articles.extend(get_articles(url))

    generate_rss(all_articles, 'rss.xml')

if __name__ == "__main__":
    main()
