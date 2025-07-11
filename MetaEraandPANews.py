#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import re # Added for regex in get_news_from_metaera

# 设定 Headless 模式
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

urls = {
    'MetaEra': 'https://www.metaera.hk/gw_search/hashkey',
    'PANews': 'https://www.panewslab.com/zh/search?query=hashkey&mode=articles',
    'TechFlow': 'https://www.techflowpost.com/search/index.html?wd=hashkey'
}

cutoff_date = datetime.now() - timedelta(days=7)

all_news = []

def get_news_from_metaera(driver):
    print("开始抓取 MetaEra...")
    driver.get(urls['MetaEra'])
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 使用与test.py相同的选择器
    boxs = soup.find_all('div', class_='search-result-box')
    if not boxs:
        print("MetaEra - 未找到search-result-box")
        return []
        
    items = boxs[0].find_all('a')
    print(f"MetaEra - 找到 {len(items)} 个新闻链接")
    results = []

    for a in items:
        try:
            title = a.text.strip()
            if not title or 'hashkey' not in title.lower():
                continue
                
            link = a['href']
            if not link.startswith('http'):
                link = 'https://www.metaera.hk' + link
                
            # MetaEra 没有在列表页显示日期
            results.append({
                'title': title,
                'url': link,
                'website': 'MetaEra',
                'publish_time': ''  # 需要点进文章才能获取时间
            })
            print(f"MetaEra - 找到新闻: {title}")
        except Exception as e:
            print(f"MetaEra - 解析失败: {e}")
            continue
            
    print(f"MetaEra - 共找到 {len(results)} 条新闻")
    return results

def get_news_from_panews(driver):
    driver.get(urls['PANews'])
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # 用 CSS Selector 匹配所有 class
    cards = soup.select('div.w-full.md\:flex.md\:flex-row.md\:items-start.md\:gap-2')
    results = []
    for card in cards:
        # 标题链接
        a_tag = card.find('a', href=True)
        if not a_tag:
            continue
        title = a_tag.text.strip()
        link = 'https://www.panewslab.com' + a_tag['href']
        # 时间
        time_tag = card.find('span')
        date_str = time_tag.text.strip() if time_tag else ''
        # 只保留近7天新闻
        try:
            post_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            if post_date >= cutoff_date:
                results.append({'title': title, 'url': link, 'website': 'PANews', 'publish_time': date_str})
        except:
            continue
    return results

def get_news_from_techflow(driver):
    print("开始抓取 TechFlow...")
    driver.get(urls['TechFlow'])
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    news_items = soup.find_all('div', class_='item')
    results = []
    
    for item in news_items:
        try:
            # 获取标题和链接
            title_tag = item.find('a', class_='tit')
            if not title_tag:
                continue
                
            title = title_tag.text.strip()
            if not title or 'hashkey' not in title.lower():
                continue
                
            link = title_tag.get('href', '')
            if link and not link.startswith('http'):
                link = 'https://www.techflowpost.com' + link
                
            # 获取时间
            time_tag = item.find('div', class_='time')
            date_str = time_tag.text.strip() if time_tag else ''
            
            # 转换日期格式
            if date_str:
                # TechFlow的日期格式通常是 "2025.07.07 - 4 天前" 这样的格式
                date_str = date_str.split(' - ')[0]  # 只取日期部分
                
            results.append({
                'title': title,
                'url': link,
                'website': 'TechFlow',
                'publish_time': date_str
            })
            print(f"TechFlow - 找到新闻: {title}")
        except Exception as e:
            print(f"TechFlow - 解析失败: {e}")
            continue
            
    print(f"TechFlow - 共找到 {len(results)} 条新闻")
    return results

def get_news_from_foresightnews(driver):
    driver.get(urls['ForesightNews'])
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cards = soup.find_all('div', class_='article-content item_article')
    results = []
    for card in cards:
        # 标题和链接
        a_tag = card.find('a', href=True)
        title_tag = card.find('div', class_='article-body-title')
        if not a_tag or not title_tag:
            continue
        title = title_tag.text.strip()
        link = 'https://foresightnews.pro' + a_tag['href']
        # 时间
        foot = card.find('div', class_='foot')
        date_str = foot.text.strip() if foot else ''
        # 只保留近7天新闻
        try:
            post_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            if post_date >= cutoff_date:
                results.append({'title': title, 'url': link, 'website': 'ForesightNews', 'publish_time': date_str})
        except:
            continue
    return results

# 在urls中添加ForesightNews
urls['ForesightNews'] = 'https://foresightnews.pro/search?search=hashkey&search_type=website&params_type=article'

# 抓取
all_news.extend(get_news_from_metaera(driver))
all_news.extend(get_news_from_panews(driver))
all_news.extend(get_news_from_techflow(driver))
all_news.extend(get_news_from_foresightnews(driver))
driver.quit()

# 保存为CSV
if all_news:
    df = pd.DataFrame(all_news)
    print(f"总新闻数量: {len(df)}")
    
    # 尝试按时间排序
    try:
        df = df.sort_values('publish_time', ascending=False)
    except:
        print("时间排序失败，保持原有顺序")
    
    # 保存所有结果，不做去重
    df.to_csv('hashkey_news.csv', index=False, encoding='utf-8-sig')
    print(f'已保存 {len(df)} 条新闻到 hashkey_news.csv')
    
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
