import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from datetime import datetime
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

class AgentGraphState(TypedDict):
    loader: Optional[str] = None
    scraper: Optional[dict] = None
    retriever: Optional[str] = None

#Initialize the state
state: AgentGraphState = ({
    "loader": None,
    "scraper": {},
    "retriever": None
})
    
#Return the HTML of the target url using AI Jina Reader API
def loader(state: AgentGraphState):

    api_url = "https://r.jina.ai/"  # Jina AI Reader API call

    headers = {
        'X-Return-Format': 'html',
        'X-Target-Selector': 'tbody'
    }

    target_url = 'gazettes.africa/gazettes/ke/2024'

    response = requests.get(api_url + target_url, headers=headers)
    state["loader"] = response.text
    
    # Print the loader content to the console for debugging
    #print("Loader content:", state["loader"])

    return {"loader": state["loader"]}

#Parses the HTML content to retreive the links
def scraper(state: AgentGraphState):
    if state["loader"]:
        html_content = state["loader"]
        soup = BeautifulSoup(html_content, 'html.parser')
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
                grouped_links[month].append({date_obj, published_date, root_url + link, root_url + sub_link})

                state["scraper"] = grouped_links
            else:
                continue

        #print("Scraper Content:", grouped_links)
        return state

# Retriever function to display the extracted data
def retriever(state: AgentGraphState):
    return state["scraper"]

# Define the workflow
workflow = StateGraph(AgentGraphState)

workflow.add_node("Loader", loader)
workflow.add_node("Scraper", scraper)
workflow.add_node("Retriever", retriever)


workflow.set_entry_point("Loader")
workflow.add_edge("Loader", "Scraper")
workflow.add_edge("Scraper", "Retriever")
workflow.add_edge("Retriever", END)


app = workflow.compile()

results = app.invoke(state)

st.write("Extracted Links and Dates:")
for published_date, link, sub_link in results:
    st.write(f"Publish date: {published_date}")
    st.write(f"Link: {link}")
    st.write(f"PDF Link: {sub_link}")
    st.write("---")


if __name__ == "__main__":
    st.write("Workflow completed!")



    