import requests
import streamlit as st
import re
from bs4 import BeautifulSoup
from datetime import datetime

def jina_webapi_scraper(target_url, headers):
    api_url = "https://r.jina.ai/"
    response = requests.get(api_url + target_url, headers=headers)
    return response.text
    

target_url = "gazettes.africa/gazettes/ke/2024"

headers = {"X-Target-Selector":"tbody", "X-Return-Format": "html"}

data = jina_webapi_scraper(target_url, headers)

# Process the HTML data if it was successfully fetched
if data:
    soup = BeautifulSoup(data, 'html.parser')
    news = soup.find_all('tr')

    root_url = "https://gazettes.africa"
    pdf_link = "/source"    
    grouped_links = {}

    for new in news:
        date_element = new.find('td')
        link_element = new.find('a')
        
        
        if date_element and link_element:
            published_date = date_element.text.strip()

            date_match = re.search(r'\d{4}-\d{2}-\d{2}', published_date)

            if date_match:
                date_str = date_match.group(0)
                
                # Convert the date string to a datetime object
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                month = date_obj.strftime('%B')  # Get month as a full name (e.g., "August")


            link = link_element.attrs['href']
            sub_link = link + pdf_link

            if month not in grouped_links:
                grouped_links[month] = []
            grouped_links[month].append((date_obj, published_date, root_url + link, root_url + sub_link))
        
        else:
            continue
        
sorted_months = sorted(grouped_links.keys(), key=lambda m: min(date[0] for date in grouped_links[m])) 


selected_month = st.selectbox("Selected month", sorted_months) 
     
st.title(f"Gazettes for {selected_month}")
if selected_month in grouped_links:
    for date_obj, published_date, link, sub_link in grouped_links[selected_month]:
        st.write(f"Publish date: {published_date}")
        st.write(f"Gazette: {sub_link}")  
        