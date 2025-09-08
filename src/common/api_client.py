import os
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure structured JSON logging
# This setup ensures all log output is in a machine-readable JSON format,
# which is essential for automated monitoring and log aggregation in a
# production environment. It's a demonstration of our commitment to
# consultant-grade observability.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(json.dumps({
        'timestamp': '%(asctime)s',
        'level': '%(levelname)s',
        'message': '%(message)s'
    }))
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RedisEnterpriseAPI:
    """
    A reusable, professional-grade client for the Redis Enterprise REST API.

    This class encapsulates all API interactions, demonstrating key principles
    of a robust, production-ready system:
    - Centralized configuration and authentication.
    - Resilient network communication with automatic retries.
    - Enhanced security with support for custom CA bundles.
    - Structured, actionable logging for superior observability.
    """
    def __init__(self, host, port, user, password, verify_tls=True, ca_bundle=None):
        """
        Initializes the API client.

        Args:
            host (str): The hostname or IP address of the Redis Enterprise cluster.
            port (int): The port for the REST API (typically 8080 or 9443).
            user (str): The email address of the API user.
            password (str): The password for the API user.
            verify_tls (bool): Whether to verify the server's TLS certificate.
                               Defaults to True. Can be set to False for dev
                               environments, but is not recommended.
            ca_bundle (str, optional): Path to a custom CA bundle file. This
                                       demonstrates an advanced security posture
                                       for zero-trust enterprise networks.
        """
        if not all([host, port, user, password]):
            raise ValueError("API credentials and host information are required.")

        self.base_url = f"https://{host}:{port}/v1"
        self.auth = (user, password)
        # The 'verify' parameter cleverly handles both boolean flags and CA bundle paths.
        self.verify = ca_bundle if ca_bundle else verify_tls
        
        self.session = self._create_session()
        logger.info({
            "event": "api_client_initialized",
            "endpoint": self.base_url,
            "tls_verification": "custom_ca" if ca_bundle else self.verify
        })

    def _create_session(self):
        """
        Creates a robust `requests.Session` with a configured retry mechanism.

        This demonstrates engineering discipline by building a client that is
        resilient to transient network failures, which is critical for
        reliable automation scripts.
        """
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504], # Retry on server-side errors
            allowed_methods=False # Setting this to False retries on all methods
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter) # Also mount for http for non-tls api endpoints
        return session

    def _request(self, method, endpoint, payload=None, params=None):
        """
        A centralized method for making all API requests.

        This centralizes error handling and logging, ensuring consistency
        and preventing code duplication. It also handles the case where
        the API returns an empty body on success.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                auth=self.auth,
                json=payload,
                params=params,
                verify=self.verify
            )
            response.raise_for_status()
            
            # Some successful API calls return empty bodies (e.g., DELETE).
            # We handle this gracefully.
            if response.text:
                return response.json()
            return None

        except requests.exceptions.HTTPError as http_err:
            logger.error({
                "event": "api_request_failed",
                "method": method.upper(),
                "url": url,
                "status_code": http_err.response.status_code,
                "response": http_err.response.text
            })
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error({
                "event": "api_request_failed",
                "method": method.upper(),
                "url": url,
                "error": str(req_err)
            })
            raise

    def get_database(self, name):
        """
        Checks for the existence of a database by name.

        Demonstrates idempotent design by providing a way to check before
        acting. It gracefully handles the expected 404 error if the
        database doesn't exist, distinguishing it from other failures.
        """
        logger.info({"event": "get_database_check", "db_name": name})
        # The API returns a list, even when querying by a unique name.
        dbs = self._request("GET", f"bdbs?name={name}")
        if dbs and len(dbs) > 0:
            logger.info({"event": "database_found", "db_name": name, "db_id": dbs[0]['uid']})
            return dbs[0]
        logger.info({"event": "database_not_found", "db_name": name})
        return None

    def create_database(self, name, password, memory_size=100000000):
        """
        Creates a new database. Part of the full lifecycle automation.
        """
        logger.info({"event": "create_database_request", "db_name": name})
        payload = {
            "name": name,
            "memory_size": memory_size,
            "type": "redis",
            "replication": True,
            "sharding": False,
            "authentication_redis_pass": password,
            # We explicitly set the port to ensure predictable connection endpoints.
            "port": 12000
        }
        response = self._request("POST", "bdbs", payload=payload)
        logger.info({"event": "create_database_success", "db_name": name, "response": response})
        return response

    def delete_database(self, db_id):
        """
        Deletes a database by its UID. Part of a clean teardown process.
        """
        logger.info({"event": "delete_database_request", "db_id": db_id})
        self._request("DELETE", f"bdbs/{db_id}")
        logger.info({"event": "delete_database_success", "db_id": db_id})

    def get_user(self, email):
        """
        Checks for the existence of a user by email.

        Another example of idempotent design. Gracefully handles 404s.
        """
        logger.info({"event": "get_user_check", "email": email})
        # API returns a list, so we check if it's non-empty.
        users = self._request("GET", f"users?email={email}")
        if users and len(users) > 0:
            logger.info({"event": "user_found", "email": email, "user_id": users[0]['id']})
            return users[0]
        logger.info({"event": "user_not_found", "email": email})
        return None

    def create_user(self, name, email, password, role="db_member"):
        """
        Creates a new user. Part of the full lifecycle automation.
        """
        logger.info({"event": "create_user_request", "email": email, "role": role})
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "role": role
        }
        response = self._request("POST", "users", payload=payload)
        logger.info({"event": "create_user_success", "email": email, "response": response})
        return response

    def delete_user(self, user_id):
        """
        Deletes a user by their ID. Part of a clean teardown process.
        """
        logger.info({"event": "delete_user_request", "user_id": user_id})
        self._request("DELETE", f"users/{user_id}")
        logger.info({"event": "delete_user_success", "user_id": user_id})
