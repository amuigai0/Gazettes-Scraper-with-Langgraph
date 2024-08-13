import requests
import streamlit as st
from bs4 import BeautifulSoup
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class AgentGraphState(TypedDict):
    loader: Optional[str] = None
    scraper: Optional[dict[List[tuple]]] = None
    retreiver: Optional[List[tuple]] = None

#Initialize the state
state: AgentGraphState = {
    "loader": None,
    "scraper": None,
    "retreiver": None
}
    
#Return the HTML of the target url using AI Jina Reader API
def loader(state):

    api_url = "https://r.jina.ai/"  # Jina AI Reader API call

    headers = {
        'X-Return-Format': 'html',
        'X-Target-Selector': 'tbody'
    }

    target_url = 'gazettes.africa/gazettes/ke/2024'
    response = requests.get(api_url + target_url, headers=headers)
    state["loader"] = response.text
    return state
    

#Parses the HTML content to retreive the links
def scraper(state):
    if state["loader"]:
        html_content = state["loader"]
        soup = BeautifulSoup(html_content, 'html.parser')
        news = soup.find_all('tr')

        root_url = "https://gazettes.africa"
        pdf_link = "/source"    

        for new in enumerate(news):
            date_element = new.find('td')
            link_element = new.find('a')
            
            
            if date_element and link_element:
                published_date = date_element.text.strip()
                link = link_element.attrs['href']
                sub_link = link + pdf_link

                state["scraper"].append((published_date, root_url + link, root_url + sub_link))
            
            else:
                continue

        return state


#Displays the list of URL links
def retreiver(state):
    st.title("Extracted Links and Dates")  
    for published_date, link, sub_link in state["scraper"]:          
        st.write(f"Publish date: {published_date}")
        st.write(f"Link: {link}")
        st.write(f"PDF Link: {sub_link}")

    return state

# Define the workflow
workflow = StateGraph(AgentGraphState)

workflow.add_node("Loader", loader)
workflow.add_node("Scraper", scraper)
workflow.add_node("Retreiver", retreiver)

workflow.set_entry_point("Loader")
workflow.add_edge("Loader", "Scraper")
workflow.add_edge("Scraper","Retreiver")

app = workflow.compile()

app.invoke()


if __name__ == "__main__":
   pass

    