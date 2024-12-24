import os
import certifi

from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def get_vector_store():
    API_KEY = os.getenv('OPENAI_API_KEY')
    MONGODB_URI = os.getenv('MONGODB_ATLAS_CLUSTER_URI')

    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    DB_NAME = 'law_tripos_rag'
    COLLECTION_NAME = 'law_tripos_collection'
    ATLAS_VECTOR_SEARCH_INDEX_NAME = 'default'

    collection = client[DB_NAME][COLLECTION_NAME]
    embedding = OpenAIEmbeddings(model='text-embedding-3-large', openai_api_key=API_KEY)

    return MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embedding,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn='cosine'
    )
