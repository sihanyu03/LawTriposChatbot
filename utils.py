import os
import certifi
import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
MONGODB_URI = os.getenv('MONGODB_ATLAS_CLUSTER_URI')

client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
DB_NAME = 'law_tripos_rag'


def check_login_details(username: str, password: str):
    COLLECTION_NAME = 'login_data'
    collection = client[DB_NAME][COLLECTION_NAME]

    result = collection.find_one({'username': username}, projection={'hashed_password': True, '_id': False})

    return result and bcrypt.checkpw(password.encode('utf-8'), result['hashed_password'].encode('utf-8'))


def get_client():
    return client


def get_vector_store():
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
