from utils import get_vector_store

import os
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


@tool(response_format='content_and_artifact')
def retrieve(query: str):
    """Retrieve information related to a query"""
    retrieved_docs = vector_store.similarity_search(query, k=3)
    serialised = '\n\n'.join(f'Source: {doc.metadata}\nContent: {doc.page_content}' for doc in retrieved_docs)
    return serialised, retrieved_docs


def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond."""
    model_with_tools = model.bind_tools([retrieve])
    response = model_with_tools.invoke(state['messages'])
    return {'messages': response}


def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state['messages']):
        if message.type == 'tool':
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = '\n\n'.join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know."
        f"\n\n{docs_content}"
    )
    conversation_messages = [
        message for message in state['messages'] if message.type in ('human', 'system') or (message.type == 'ai' and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = model.invoke(prompt)
    return {'messages': [response]}


load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

vector_store = get_vector_store()

model = ChatOpenAI(model='gpt-4o-mini', openai_api_key=API_KEY)
graph_builder = StateGraph(MessagesState)

graph_builder.add_node(query_or_respond)
graph_builder.add_node(ToolNode([retrieve]))
graph_builder.add_node(generate)

graph_builder.set_entry_point('query_or_respond')
graph_builder.add_conditional_edges('query_or_respond', tools_condition, {END: END, 'tools': 'tools'})
graph_builder.add_edge('tools', 'generate')
graph_builder.add_edge('generate', END)

# graph = graph_builder.compile()
graph = graph_builder.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "abc123"}}


def generate_response(query: str):
    final_state = graph.invoke(
        {'messages': [{'role': 'user', 'content': query}]},
        config=config
    )

    if len(final_state['messages']) < 2:
        raise RuntimeError('Length of the messages produced is less than 2')

    tool_msg = final_state['messages'][-2]
    if not isinstance(tool_msg, ToolMessage):
        file = None
        page = None
    else:
        try:
            start_idx = tool_msg.content.index("'source': '")
            end_idx = tool_msg.content.index(',', start_idx)
            file = tool_msg.content[start_idx + 11: end_idx]
        except ValueError:
            file = None

        try:
            start_idx = tool_msg.content.index("'page': ")
            end_idx = tool_msg.content.index(',', start_idx)
            page = int(tool_msg.content[start_idx + 8: end_idx]) + 1
        except ValueError:
            page = None

    ai_msg = final_state['messages'][-1]
    if not isinstance(ai_msg, AIMessage):
        raise RuntimeError('Last message was not of type AIMessage')

    response = ai_msg.content

    return {'file': file, 'page': page, 'response': response}


if __name__ == '__main__':
    print(generate_response("Give a very short summary of Sumpton vs Hoffman"))
    print(generate_response("What was my previous question?"))