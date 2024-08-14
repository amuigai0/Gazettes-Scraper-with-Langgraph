import requests
import streamlit as st
from bs4 import BeautifulSoup
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class AgentGraphState(TypedDict):
    loader: Optional[str] = None
    scraper: List[tuple] = None

#Initialize the state
state: AgentGraphState = {
    "loader": None,
    "scraper": []
}
    
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

    return {"loader": state["loader"], "scraper": []}

#Parses the HTML content to retreive the links
def scraper(state: AgentGraphState):
    if state["loader"]:
        state["scraper"] = []
        html_content = state["loader"]
        soup = BeautifulSoup(html_content, 'html.parser')
        news = soup.find_all('tr')

        root_url = "https://gazettes.africa"
        pdf_link = "/source"    

        for new in news:
            date_element = new.find('td')
            link_element = new.find('a')
            
            
            if date_element and link_element:
                published_date = date_element.text.strip()
                link = link_element.attrs['href']
                sub_link = link + pdf_link

                state["scraper"].append((published_date, root_url + link, root_url + sub_link))
            
            else:
                continue

        #print("Scraper Content:", state["scraper"])
        return state

# Retriever function to display the extracted data
def retriever(state: AgentGraphState):
    return state["scraper"]

# Define the workflow
workflow = StateGraph(AgentGraphState)

workflow.add_node("Loader", loader)
workflow.add_node("Scraper", scraper)
workflow.add_node("Retreiver", retriever)


workflow.set_entry_point("Loader")
workflow.add_edge("Loader", "Scraper")
workflow.add_edge("Scraper", "Retreiver")


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



    