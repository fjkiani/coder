import os
import redis
import logging
from dotenv import load_dotenv

# --- Configuration & Setup ---
load_dotenv()

# Configure logging to match the common client's style for consistency
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Main Execution ---
def main():
    """
    Executes the core logic for Exercise 1:
    1. Connects to the primary and replica Redis instances.
    2. Ingests a list of phrases into a Redis List using a pipeline.
    3. Validates the data was written correctly to the primary.
    4. Reads the data from the replica to verify replication.
    5. Prints the required output: reverse-ordered values from the replica.
    """
    logging.info("Starting Exercise 1: Redis Fundamentals and Replication.")

    # Load configuration from environment variables
    # This demonstrates our commitment to security by never hard-coding credentials.
    primary_host = os.getenv("SOURCE_DB_HOST", "localhost")
    primary_port = int(os.getenv("SOURCE_DB_PORT", 12000))
    replica_host = os.getenv("REPLICA_DB_HOST", "localhost")
    replica_port = int(os.getenv("REPLICA_DB_PORT", 12000))
    # The instructions specify passwordless dbs for this exercise.
    db_password = os.getenv("EX1_DB_PASSWORD", None)
    # This flag allows us to disable TLS verification for lab environments.
    verify_tls = os.getenv("VERIFY_TLS", "true").lower() == "true"
    # This flag allows us to disable SSL entirely for non-TLS endpoints.
    use_ssl = os.getenv("USE_SSL", "true").lower() == "true"

    # Data to be ingested.
    # Per the instructions, we are inserting the numbers 1-100.
    key_name = "exercise:1:data"
    values_to_insert = list(range(1, 101))

    try:
        # Connect to both primary and replica nodes
        # We build a robust configuration that handles TLS verification gracefully.
        redis_kwargs = {
            "decode_responses": True,
        }
        if use_ssl:
            redis_kwargs["ssl"] = True
            redis_kwargs["ssl_cert_reqs"] = "required" if verify_tls else None
        
        if db_password:
            redis_kwargs["password"] = db_password

        primary_redis = redis.Redis(host=primary_host, port=primary_port, **redis_kwargs)
        primary_redis.ping()
        logging.info(f"Successfully connected to source-db at {primary_host}:{primary_port}")

        replica_redis = redis.Redis(host=replica_host, port=replica_port, **redis_kwargs)
        replica_redis.ping()
        logging.info(f"Successfully connected to replica-db at {replica_host}:{replica_port}")
        
        # --- Get ReplicaOf info for validation output ---
        replica_info = replica_redis.info("replication")
        source_host = replica_info.get("master_host", "UNKNOWN")
        source_port = replica_info.get("master_port", "UNKNOWN")

        # Clean up any previous runs to ensure a clean slate
        primary_redis.delete(key_name)
        logging.info(f"Cleared key '{key_name}' from previous runs.")

        # --- Ingest Data using a Pipeline ---
        # Using a pipeline is a best practice for batch operations. It minimizes
        # network round-trips, significantly improving performance.
        logging.info(f"Ingesting {len(values_to_insert)} numbers into Redis List '{key_name}'.")
        pipe = primary_redis.pipeline()
        for val in values_to_insert:
            pipe.rpush(key_name, val)
        pipe.execute()

        # --- Validate on Primary ---
        count = primary_redis.llen(key_name)
        if count == len(values_to_insert):
            logging.info(f"Validation successful: Found {count} items in '{key_name}' on the source.")
        else:
            logging.error(f"Validation FAILED: Expected {len(values_to_insert)} items, but found {count}.")
            return

        # --- Read from Replica and Produce Final Output ---
        # The core validation step: can we read the replicated data?
        logging.info(f"Fetching values from replica to verify replication.")
        replicated_values = replica_redis.lrange(key_name, 0, -1)
        
        print("\n--- Exercise 1 Validation Output ---")
        print(f"Reading from replica-db at: {replica_host}:{replica_port}")
        print(f"Replica reports source at: {source_host}:{source_port}")
        print("Values in reverse order:")
        for value in reversed(replicated_values):
            print(f"- {value}")
        print("------------------------------------")

    except redis.exceptions.ConnectionError as e:
        logging.error(f"Redis connection failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
