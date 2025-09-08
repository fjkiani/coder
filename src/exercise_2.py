import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path to allow for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.api_client import RedisEnterpriseAPI, logger

# --- Configuration ---
load_dotenv()

DB_NAME = "exercise-2-db"
# User data now reflects the exact requirements from the mission instructions.
USERS = [
    {"name": "John Doe", "email": "john.doe@example.com", "role": "db_viewer"},
    {"name": "Mike Smith", "email": "mike.smith@example.com", "role": "db_member"},
    {"name": "Cary Johnson", "email": "cary.johnson@example.com", "role": "admin"},
]
DB_PASSWORD = os.getenv("RE_DB_PASSWORD")


def manage_database(api: RedisEnterpriseAPI):
    """
    Idempotently creates the database required for the exercise.
    """
    logger.info(f"--- Managing Database: {DB_NAME} ---")
    db = api.get_database(DB_NAME)
    if db:
        db_id = db.get('uid')
        logger.info(f"SUCCESS: Database '{DB_NAME}' already exists with ID: {db_id}.")
        print(f"Database '{DB_NAME}' (ID: {db_id}) already exists.")
    else:
        logger.info(f"Database '{DB_NAME}' not found. Creating it now.")
        if not DB_PASSWORD:
            raise ValueError("FATAL: RE_DB_PASSWORD must be set to create a database.")
        response = api.create_database(DB_NAME, DB_PASSWORD)
        db_id = response.get('uid')
        logger.info(f"SUCCESS: Created database '{DB_NAME}' with ID: {db_id}.")
        print(f"Database '{DB_NAME}' created with ID: {db_id}.")


def manage_users(api: RedisEnterpriseAPI):
    """
    Idempotently creates the users required for the exercise.
    """
    logger.info("--- Managing Users ---")
    print("\nVerifying Users:")
    for user_def in USERS:
        user = api.get_user(user_def["email"])
        if user:
            logger.info(f"SUCCESS: User '{user_def['email']}' already exists.")
            print(f"- User '{user_def['email']}' already configured.")
        else:
            logger.info(f"User '{user_def['email']}' not found. Creating now.")
            if not DB_PASSWORD:
                 raise ValueError("FATAL: RE_DB_PASSWORD must be set to create users.")
            api.create_user(user_def["name"], user_def["email"], DB_PASSWORD, user_def["role"])
            logger.info(f"SUCCESS: Created user '{user_def['email']}'.")
            print(f"- User '{user_def['email']}' created.")

    print("\n--- User Validation Output ---")
    print("name, role, email")
    for user_def in USERS:
        print(f"{user_def['name']}, {user_def['role']}, {user_def['email']}")
    print("----------------------------")


def teardown_resources(api: RedisEnterpriseAPI):
    """
    Cleans up all resources created by this script.
    """
    logger.info("--- Starting resource teardown ---")
    print("--- Tearing Down Resources ---")

    # Delete users first
    for user_def in USERS:
        user = api.get_user(user_def["email"])
        if user:
            # Use direct key access for clarity and immediate failure if key is missing.
            user_id = user['uid']
            logger.info(f"Deleting user '{user_def['email']}' (UID: {user_id}).")
            api.delete_user(user_id)
            print(f"- User '{user_def['email']}' deleted.")
        else:
            logger.info(f"User '{user_def['email']}' already gone. Skipping.")
            print(f"- User '{user_def['email']}' not found.")

    # Delete the database
    db = api.get_database(DB_NAME)
    if db:
        # Use direct key access here as well for consistency.
        db_id = db['uid']
        logger.info(f"Deleting database '{DB_NAME}' (UID: {db_id}).")
        api.delete_database(db_id)
        print(f"- Database '{DB_NAME}' deleted.")
    else:
        logger.info(f"Database '{DB_NAME}' already gone. Skipping.")
        print(f"- Database '{DB_NAME}' not found.")
    
    print("----------------------------")


def main():
    """
    Main execution block.
    Parses command-line arguments to run 'setup' or 'teardown'.
    """
    if len(sys.argv) != 2 or sys.argv[1] not in ["setup", "teardown"]:
        print("Usage: python exercise_2.py [setup|teardown]")
        sys.exit(1)

    action = sys.argv[1]

    # Initialize the API client from environment variables
    try:
        api_client = RedisEnterpriseAPI(
            host=os.getenv("RE_HOST"),
            port=int(os.getenv("RE_PORT")),
            user=os.getenv("RE_API_USER"),
            password=os.getenv("RE_API_PASSWORD"),
            verify_tls=(os.getenv("VERIFY_TLS", "true").lower() == "true"),
            ca_bundle=os.getenv("CUSTOM_CA_BUNDLE_PATH")
        )
    except (ValueError, TypeError) as e:
        logger.error(f"FATAL: Failed to initialize API client. Check environment variables. Error: {e}")
        sys.exit(1)

    try:
        if action == "setup":
            print("\n--- Running Setup ---")
            manage_database(api_client)
            manage_users(api_client)
            print("\nSetup complete.")
        elif action == "teardown":
            print("\n--- Running Teardown ---")
            teardown_resources(api_client)
            print("\nTeardown complete.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during '{action}': {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
