import utils
from models import ResponseModel

import re
import ast
import os
import asyncio
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver


@tool(response_format='content_and_artifact')
def retrieve(query: str):
    """Retrieve information related to a query"""
    retrieved_docs = vector_store.similarity_search(query, k=int(os.getenv('NUM_DOCUMENTS')))
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

vector_store = utils.get_vector_store()

model = ChatOpenAI(model='gpt-4o-mini', openai_api_key=API_KEY)
graph_builder = StateGraph(MessagesState)

graph_builder.add_node(query_or_respond)
graph_builder.add_node(ToolNode([retrieve]))
graph_builder.add_node(generate)

graph_builder.set_entry_point('query_or_respond')
graph_builder.add_conditional_edges('query_or_respond', tools_condition, {END: END, 'tools': 'tools'})
graph_builder.add_edge('tools', 'generate')
graph_builder.add_edge('generate', END)

checkpointer = MongoDBSaver(utils.get_client())
graph = graph_builder.compile(checkpointer=checkpointer)


async def generate_answer(query: str, thread_id: str):
    final_state = await asyncio.to_thread(
        graph.invoke,
        {'messages': [{'role': 'user', 'content': query}]},
        config={'configurable': {'thread_id': thread_id}}
    )

    if len(final_state['messages']) < 2:
        raise RuntimeError('Length of the messages produced is less than 2')

    tool_msg = final_state['messages'][-2]
    context = []

    if isinstance(tool_msg, ToolMessage):
        src = tool_msg.content
        pattern = r'Source:\s*({.*?})'
        matches = re.findall(pattern, src)
        if matches:
            dict_list = [ast.literal_eval(match) for match in matches]
            for elem in dict_list:
                if 'source' not in elem or 'page' not in elem:
                    continue
                context.append((elem['source'], elem['page'] + 1))

    ai_msg = final_state['messages'][-1]
    if not isinstance(ai_msg, AIMessage):
        raise RuntimeError('Last message was not of type AIMessage')

    answer = ai_msg.content
    context.sort()
    if context:
        files, pages = zip(*context)
    else:
        files, pages = [], []

    return ResponseModel(files=files, pages=pages, answer=answer)


def clear_thread_id_history(thread_id: str):
    client = utils.get_client()
    checkpoint_writes_collection = client['checkpointing_db']['checkpoint_writes']
    checkpoints_collection = client['checkpointing_db']['checkpoints']
    checkpoint_writes_collection.delete_many({'thread_id': thread_id})
    checkpoints_collection.delete_many({'thread_id': thread_id})
