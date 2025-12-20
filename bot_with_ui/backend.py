from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated
from langgraph.checkpoint.memory import MemorySaver
import os
import operator
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
load_dotenv()


groq_api_key=os.getenv("GROQ_API_KEY")
llm = ChatGroq(groq_api_key=groq_api_key,model_name="llama-3.1-8b-instant")


class bot_State(TypedDict):

    messages : Annotated[list[BaseMessage],add_messages]

def chat_node(state : bot_State):
    messages = state['messages']

    reponse = llm.invoke(messages)

    return {"messages":[reponse]}

graph = StateGraph(bot_State)

checkpointer = MemorySaver()
graph.add_node("chat_node",chat_node)
graph.add_edge(START,"chat_node")
graph.add_edge("chat_node",END)

chatbot = graph.compile(checkpointer=checkpointer)