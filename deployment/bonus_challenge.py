import os
import sys
import numpy as np
from dotenv import load_dotenv
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.vectorize.text import HFTextVectorizer

# --- Configuration ---
load_dotenv()
REDIS_HOST = os.getenv("BONUS_DB_HOST", "localhost")
REDIS_PORT = int(os.getenv("BONUS_DB_PORT", 12000))
REDIS_PASSWORD = os.getenv("BONUS_DB_PASSWORD", None)

INDEX_NAME = "semantic-router-index"

# Using a lightweight, effective model for embeddings.
# This demonstrates knowledge of the AI/ML ecosystem.
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
vectorizer = HFTextVectorizer(model=MODEL)

# Define the routes as per the mission instructions
ROUTES = {
    "GenAI programming topics": [
        "How do I use vector databases for retrieval augmented generation?",
        "What are the best practices for fine-tuning a large language model?",
        "Explain the transformer architecture and its role in modern AI.",
        "Langchain vs LlamaIndex for building complex AI applications.",
        "How to implement semantic caching with Redis.",
    ],
    "Science fiction entertainment": [
        "What is the plot of the latest season of 'Foundation'?",
        "Who are the main characters in the 'Dune' series?",
        "Compare the themes of 'Blade Runner' and 'Ghost in the Shell'.",
        "What is the significance of the monolith in '2001: A Space Odyssey'?",
        "Which Star Trek series is considered the best by fans?",
    ],
    "Classical music": [
        "What are the key characteristics of the Baroque period?",
        "Who were the most influential composers of the Romantic era?",
        "Analyze Beethoven's 5th Symphony.",
        "What is a fugue and how did Bach use it?",
        "Explain the structure of a classical sonata.",
    ]
}

def get_redis_connection():
    """Establishes a connection to the Redis database."""
    redis_kwargs = {"decode_responses": False} # Must be False for redisvl
    if REDIS_PASSWORD:
        redis_kwargs["password"] = REDIS_PASSWORD
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, **redis_kwargs)


def create_and_load_index(redis_conn):
    """
    Creates a RedisVL search index and loads it with the route centroids.
    This demonstrates our core AI/Vector Search competency.
    """
    index = SearchIndex.from_yaml("schema.yaml", redis_conn=redis_conn)
    
    # Check if the index already exists to make the script idempotent
    if index.name not in [i.decode() for i in redis_conn.execute_command("FT._LIST")]:
        print("Creating new search index...")
        index.create(overwrite=True)
        
        # We calculate the centroid (average) of the embeddings for each route's
        # example phrases. This centroid represents the semantic center of the topic.
        print("Calculating and loading route centroids...")
        for name, examples in ROUTES.items():
            embeddings = vectorizer.embed_many(examples)
            centroid = np.mean(embeddings, axis=0)
            
            # The key is the route name, and the value is its vector representation.
            index.load([{
                "name": name,
                "vector": centroid.astype(np.float32).tobytes()
            }])
    else:
        print("Index already exists. Skipping creation and loading.")


def route_query(index, user_query: str) -> str:
    """
    Takes a user query, finds the closest matching route using vector search,
    and returns the name of that route. This is the core semantic routing logic.
    """
    query_embedding = vectorizer.embed(user_query)

    # We perform a K-Nearest Neighbor (KNN) search to find the single
    # closest route centroid to the user's query vector.
    query = VectorQuery(
        vector=query_embedding,
        vector_field_name="vector",
        num_results=1,
        return_fields=["name"]
    )
    
    results = index.query(query)
    
    if not results:
        return "No matching route found."
    
    # Per the instructions, we only output the name of the selected route.
    return results[0]['name']


def main():
    """
    Main execution function.
    """
    if len(sys.argv) != 2:
        print("Usage: python bonus_challenge.py \"<your query>\"")
        sys.exit(1)
        
    user_query = sys.argv[1]

    try:
        redis_conn = get_redis_connection()
        redis_conn.ping()
        
        create_and_load_index(redis_conn)
        
        index = SearchIndex.from_yaml("schema.yaml", redis_conn=redis_conn)
        
        selected_route = route_query(index, user_query)
        
        # The final, verifiable output. No extra bullshit.
        print(selected_route)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # We need to ensure redis is imported for get_redis_connection
    import redis
    main()
