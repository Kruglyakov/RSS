import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET

# Функция для получения данных с сайта
def get_articles(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []

    # Ищем все элементы с новыми статьями
    for item in soup.find_all('article'):
        title = item.find('h2').get_text(strip=True)
        link = item.find('a')['href']
        pub_date = item.find('time')['datetime']
        
        # Конвертируем строку в дату
        pub_date = datetime.datetime.fromisoformat(pub_date)
        if pub_date > datetime.datetime.now() - datetime.timedelta(days=30):
            articles.append({'title': title, 'link': link, 'pub_date': pub_date})

    return articles

# Генерация RSS
def generate_rss(articles, filename):
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')

    ET.SubElement(channel, 'title').text = 'CFTS.org.ua — Новости, Статьи, Аналитика'
    ET.SubElement(channel, 'link').text = 'https://cfts.org.ua/'
    ET.SubElement(channel, 'description').text = 'Последние новости, статьи и аналитика'
    ET.SubElement(channel, 'language').text = 'ru'

    for article in articles:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = article['title']
        ET.SubElement(item, 'link').text = article['link']
        ET.SubElement(item, 'pubDate').text = article['pub_date'].strftime('%a, %d %b %Y %H:%M:%S +0000')

    tree = ET.ElementTree(rss)
    tree.write(filename)

# Основной процесс
def main():
    urls = [
        'https://cfts.org.ua/news/',
        'https://cfts.org.ua/articles/',
        'https://cfts.org.ua/analytics/'
    ]
    
    all_articles = []
    
    for url in urls:
        articles = get_articles(url)
        all_articles.extend(articles)

    generate_rss(all_articles, 'rss.xml')

if __name__ == "__main__":
    main()
