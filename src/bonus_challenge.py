import os
import sys
import numpy as np
import redis
from dotenv import load_dotenv
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
    # Use decode_responses=False because vectors are stored/retrieved as bytes
    redis_kwargs = {"decode_responses": False}
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
    try:
        # If FT.INFO succeeds, the index exists
        redis_conn.execute_command("FT.INFO", INDEX_NAME)
        print("Index already exists. Skipping creation and loading.")
    except redis.exceptions.ResponseError:
        print("Creating new search index...")
        # Create index with raw RediSearch command to ensure compatibility with redis-py 4.1.0
        # FT.CREATE semantic-router-index ON HASH PREFIX 1 route: SCHEMA name TEXT vector VECTOR FLAT 6 TYPE FLOAT32 DIM 384 DISTANCE_METRIC COSINE
        redis_conn.execute_command(
            "FT.CREATE",
            INDEX_NAME,
            "ON", "HASH",
            "PREFIX", 1, "route:",
            "SCHEMA",
            "name", "TEXT",
            "vector", "VECTOR", "FLAT", 6,
            "TYPE", "FLOAT32",
            "DIM", 384,
            "DISTANCE_METRIC", "COSINE",
        )

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

    # Perform raw FT.SEARCH with KNN to ensure compatibility across client versions
    # FT.SEARCH index "*=>[KNN 1 @vector $query_vec AS score]" PARAMS 2 query_vec <bytes> SORTBY score RETURN 2 name score DIALECT 2
    try:
        raw = redis_conn.execute_command(
            "FT.SEARCH",
            INDEX_NAME,
            "*=>[KNN 1 @vector $query_vec AS score]",
            "PARAMS", 2, "query_vec", query_embedding.tobytes(),
            "SORTBY", "score",
            "RETURN", 2, "name", "score",
            "DIALECT", 2,
        )
    except redis.exceptions.ResponseError:
        return "No matching route found."

    # raw format: [total, doc_id, [field, value, ...], ...]
    if not raw or raw[0] == 0:
        return "No matching route found."

    fields = raw[2] if len(raw) >= 3 else None
    if not isinstance(fields, (list, tuple)):
        return "No matching route found."

    route_name = None
    for i in range(0, len(fields), 2):
        key = fields[i]
        val = fields[i + 1] if i + 1 < len(fields) else None
        if key == b"name" or key == "name":
            route_name = val
            break

    if isinstance(route_name, bytes):
        route_name = route_name.decode("utf-8", errors="ignore")
    return route_name or "No matching route found."

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
