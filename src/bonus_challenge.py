import os
import sys
import numpy as np
import redis
from dotenv import load_dotenv
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

# --- Configuration ---
load_dotenv()
REDIS_HOST = os.getenv("BONUS_DB_HOST", "localhost")
REDIS_PORT = int(os.getenv("BONUS_DB_PORT", 12000))
REDIS_PASSWORD = os.getenv("BONUS_DB_PASSWORD", None)
USE_SSL = os.getenv("USE_SSL", "true").lower() == "true"

INDEX_NAME = "semantic-router-index"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Define the routes as per the mission instructions
ROUTES = {
    "GenAI programming topics": [
        "How do I use vector databases for retrieval augmented generation?",
        "What are the best practices for fine-tuning a large language model?",
    ],
    "Science fiction entertainment": [
        "What is the plot of the latest season of 'Foundation'?",
        "Who are the main characters in the 'Dune' series?",
    ],
    "Classical music": [
        "What are the key characteristics of the Baroque period?",
        "Who were the most influential composers of the Romantic era?",
    ]
}

def get_redis_connection():
    """Establishes a connection to the Redis database."""
    redis_kwargs = {"decode_responses": True}
    if USE_SSL:
        redis_kwargs["ssl"] = True
        redis_kwargs["ssl_cert_reqs"] = None
    if REDIS_PASSWORD:
        redis_kwargs["password"] = REDIS_PASSWORD
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, **redis_kwargs)

def create_and_load_index(redis_conn, vectorizer):
    """
    Creates a RediSearch index and loads it with the route centroids.
    This demonstrates our core AI/Vector Search competency using low-level commands.
    """
    schema = (
        TextField("name"),
        VectorField("vector", "FLAT", {
            "TYPE": "FLOAT32",
            "DIM": 384,
            "DISTANCE_METRIC": "COSINE"
        })
    )
    try:
        redis_conn.ft(INDEX_NAME).info()
        print("Index already exists. Skipping creation and loading.")
    except redis.exceptions.ResponseError:
        print("Creating new search index...")
        redis_conn.ft(INDEX_NAME).create_index(fields=schema)

        print("Calculating and loading route centroids...")
        for name, examples in ROUTES.items():
            embeddings = vectorizer.encode(examples)
            centroid = np.mean(embeddings, axis=0).astype(np.float32)
            
            redis_conn.hset(f"route:{name.replace(' ', '_')}", mapping={
                "name": name,
                "vector": centroid.tobytes()
            })

def route_query(redis_conn, vectorizer, user_query: str) -> str:
    """
    Takes a user query, finds the closest matching route using a raw vector query,
    and returns the name of that route.
    """
    query_embedding = vectorizer.encode(user_query).astype(np.float32)

    # This is a raw K-Nearest Neighbor (KNN) query against the index.
    # It demonstrates a deep understanding of how RediSearch works under the hood.
    q = Query("*=>[KNN 1 @vector $query_vec as score]")\
        .sort_by("score")\
        .return_fields("name", "score")\
        .dialect(2)

    query_params = {"query_vec": query_embedding.tobytes()}
    results = redis_conn.ft(INDEX_NAME).search(q, query_params)
    
    if not results.docs:
        return "No matching route found."
    
    return results.docs[0].name

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} \"<your query>\"")
        sys.exit(1)
    user_query = sys.argv[1]

    try:
        redis_conn = get_redis_connection()
        redis_conn.ping()
        
        print("Loading embedding model...")
        vectorizer = SentenceTransformer(MODEL)
        
        create_and_load_index(redis_conn, vectorizer)
        
        selected_route = route_query(redis_conn, vectorizer, user_query)
        
        print(selected_route)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
