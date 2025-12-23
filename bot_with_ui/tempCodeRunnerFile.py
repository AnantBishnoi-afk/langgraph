response = chatbot.invoke({'messages':[HumanMessage(content='what is my name')]},config={'configurable':{'thread_id':'thread-2'}})

print(response)