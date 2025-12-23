from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated
from langgraph.checkpoint.sqlite import SqliteSaver
import os
import operator
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage,AIMessage
import sqlite3
import requests
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode,tools_condition


load_dotenv()


groq_api_key=os.getenv("GROQ_API_KEY")
llm = ChatGroq(groq_api_key=groq_api_key,model_name="llama-3.1-8b-instant")


################### tools

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num : float, second_num :float , operation : str) ->dict:
    """
    perform a basic arithmetic operationon two numbers.
    supported operation : add, sub, mul, div"""

    try :
        if operation=="add":
            result= first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num*second_num
        elif operation == "div":
            if(second_num==0):
                return {"error":"divison by zero is not allowed"}
            result = first_num/second_num
        else:
            return{"error":f"unsupported action:'{operation}'"}
        return{"first_num":first_num,"second_num":second_num,"operation":operation,"result":result}
    except Exception as e:
        return {"error":str(e)}

tools = [search_tool,calculator]

llm_with_tools = llm.bind_tools(tools)




class bot_State(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]

###################### defining nodes
def chat_node(state : bot_State):
    """LLM node that may answer or request a tool call."""
    messages = state['messages']

    reponse = llm_with_tools.invoke(messages)

    return {"messages":[reponse]}

tool_node = ToolNode(tools)

################ database connection

graph = StateGraph(bot_State)
conn = sqlite3.connect(database='database.db',check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

############## graph node creation and connection

graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)

graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge("tools","chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

# response = chatbot.invoke({'messages':[HumanMessage(content='what is my name')]},config={'configurable':{'thread_id':'thread-1'}})

# print(response)
# print(chatbot.get_state(config={'configurable':{'thread_id' :'thread-1'}}).values['messages'])

def retrieve_all_threads():
    all_threads = set()
    for chk in checkpointer.list(None):
        all_threads.add(chk.config['configurable']['thread_id'])

    return list(all_threads)


