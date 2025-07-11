from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import re

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

driver = webdriver.Chrome(options=options)
cutoff_date = datetime.now() - timedelta(days=7)
all_news = []

def extract_date(text):
    # 提取日期的通用函数
    date_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}|\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2})'
    match = re.search(date_pattern, text)
    return match.group(1) if match else ''

def get_news_from_panews(driver):
    print("开始抓取 PANews...")
    driver.get('https://www.panewslab.com/zh/search?query=hashkey&mode=articles')
    time.sleep(10)
    
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = []
    
    # 查找所有新闻容器
    containers = soup.find_all('div', class_='w-full')
    for container in containers:
        try:
            title_text = container.text.strip()
            if 'hashkey' not in title_text.lower():
                continue
                
            # 提取标题（去除时间和其他信息）
            title = title_text.split('2025-')[0].strip()
            if not title:
                continue
                
            # 提取时间
            date_str = extract_date(title_text)
            if not date_str:
                continue
                
            # 提取链接
            link = container.find('a')
            if link and link.get('href'):
                url = 'https://www.panewslab.com' + link['href']
            else:
                continue
                
            results.append({
                'title': title,
                'url': url,
                'publish_time': date_str,
                'website': 'PANews'
            })
            print(f"PANews - 找到新闻: {title}")
            
        except Exception as e:
            print(f"PANews - 解析失败: {e}")
            continue
            
    return results

def get_news_from_foresightnews(driver):
    print("开始抓取 ForesightNews...")
    driver.get('https://foresightnews.pro/search?search=hashkey&search_type=website&params_type=article')
    time.sleep(10)
    
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = []
    
    # 查找所有新闻容器
    containers = soup.find_all('div', class_='article-content item_article')
    for container in containers:
        try:
            title_text = container.text.strip()
            if 'hashkey' not in title_text.lower():
                continue
                
            # 提取标题（去除多余信息）
            title = title_text.split('2025-')[0].strip()
            if not title:
                continue
                
            # 提取时间
            date_str = extract_date(title_text)
            if not date_str:
                continue
                
            # 提取链接
            link = container.find('a')
            if link and link.get('href'):
                url = 'https://foresightnews.pro' + link['href']
            else:
                continue
                
            results.append({
                'title': title,
                'url': url,
                'publish_time': date_str,
                'website': 'ForesightNews'
            })
            print(f"ForesightNews - 找到新闻: {title}")
            
        except Exception as e:
            print(f"ForesightNews - 解析失败: {e}")
            continue
            
    return results

try:
    # 抓取
    all_news.extend(get_news_from_panews(driver))
    all_news.extend(get_news_from_foresightnews(driver))
finally:
    driver.quit()

# 保存结果
if all_news:
    df = pd.DataFrame(all_news)
    df = df.drop_duplicates(subset=['title', 'url'])  # 去重
    df = df.sort_values('publish_time', ascending=False)  # 按时间排序
    df.to_csv('PANewsandForesightNews.csv', index=False, encoding='utf-8-sig')
    print(f'已保存 {len(df)} 条新闻到 PANewsandForesightNews.csv')
    
    # 显示前5条新闻作为示例     
    print("\n最新的5条新闻:")
    for _, row in df.head().iterrows():
        print(f"标题: {row['title']}")
        print(f"链接: {row['url']}")
        print(f"时间: {row['publish_time']}")
        print(f"来源: {row['website']}")
        print("-" * 50)
else:
    print('没有抓到新闻')
