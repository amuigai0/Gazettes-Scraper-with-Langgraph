#States testing

"""from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

# Define the state object for the agent graph
class AgentGraphState(TypedDict):
    loader_response: Annotated[list, add_messages] #Loader state to retreive the URL
    analyzer_response: Annotated[list, add_messages] #Checks sub-links of retreived links from scraper 
    scraper_response: Annotated[list, add_messages] #Retreives HTML Tags of Gazette links
    retreiver_response: Annotated[list, add_messages] #Gets the pdf links
    end_chain: Annotated[list, add_messages]

# Define the nodes in the agent graph
def get_agent_graph_state(state:AgentGraphState, state_key:str):
    if state_key == "loader_all":
        return state["loader_response"]
    
    elif state_key == "analyzer_all":
        return state["analyzer_response"]

    
    elif state_key == "retreiver_all":
        return state["retreiver_response"]

    
    elif state_key == "scraper_all":
        return state["scraper_response"]
        
    else:
        return None
    
state = {
    "loader_response": [],
    "analyzer_response": [],
    "retreiver_response": [],
    "scraper_response": [],
    "end_chain": []
}"""