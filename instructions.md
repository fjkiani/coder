## How to Run and Validate the Technical Challenge (Customer Instructions)

### Environment and Repository
- IDE terminal: [Open IDE terminal](https://code-dot-rl-s-tc-fjk.labs.ps-redis.com/?folder=/home/coder)
- Repository: [https://github.com/fjkiani/coder](https://github.com/fjkiani/coder)

### One-time setup (in the IDE terminal)
```bash
cd /home/coder
if [ -d coder ]; then cd coder && git fetch origin && git reset --hard origin/main; else git clone https://github.com/fjkiani/coder.git coder && cd coder; fi
python3 -m pip install --user -r requirements.txt
```

### Exercise 1: Replication fundamentals
1) Configure endpoints (no password, non-TLS):
```bash
sed -i.bak '/^SOURCE_DB_HOST=/d;/^SOURCE_DB_PORT=/d;/^REPLICA_DB_HOST=/d;/^REPLICA_DB_PORT=/d;/^USE_SSL=/d' .env
echo "SOURCE_DB_HOST=172.16.22.21" >> .env
echo "SOURCE_DB_PORT=17159" >> .env
echo "REPLICA_DB_HOST=172.16.22.23" >> .env
echo "REPLICA_DB_PORT=13047" >> .env
echo "USE_SSL=false" >> .env
```
2) Run and validate:
```bash
python3 src/exercise_1.py
```
Expected: prints values 100→1 from replica and shows “Replica reports source at: 172.16.22.21:17159”.

### Exercise 2: REST API automation (DB and users)
1) Configure API (self‑signed TLS handled):
```bash
sed -i.bak '/^RE_HOST=/d;/^RE_PORT=/d;/^RE_API_USER=/d;/^RE_API_PASSWORD=/d;/^RE_DB_PASSWORD=/d;/^VERIFY_TLS=/d' .env
echo "RE_HOST=re-cluster1.ps-redislabs.org" >> .env
echo "RE_PORT=9443" >> .env
echo "RE_API_USER=admin@rl.org" >> .env
echo "RE_API_PASSWORD=n3Y2Cg9" >> .env
echo "RE_DB_PASSWORD=ZetaRealmRules2025!" >> .env
echo "VERIFY_TLS=false" >> .env
```
2) Run setup (idempotent):
```bash
python3 src/exercise_2.py setup
```
3) Run teardown:
```bash
python3 src/exercise_2.py teardown
```
Expected: setup reports DB ID and creates 3 users; teardown deletes users then the DB. If the environment exposes only the Admin role via `/v1/roles`, the client substitutes the available role UID with structured logs.

### Bonus: Semantic Router (Vector Search)
1) Configure bonus DB (non‑TLS):
```bash
sed -i.bak '/^BONUS_DB_HOST=/d;/^BONUS_DB_PORT=/d;/^USE_SSL=/d' .env
echo "BONUS_DB_HOST=172.16.22.22" >> .env
echo "BONUS_DB_PORT=13867" >> .env
echo "USE_SSL=false" >> .env
```
2) Run examples:
```bash
python3 src/bonus_challenge.py "How do I use vector databases for RAG?"
python3 src/bonus_challenge.py "What are the core themes of Dune?"
```
Expected routes: “GenAI programming topics” and “Science fiction entertainment”. Implementation uses low‑level RediSearch FT commands; an offline embedding fallback is included if the model cannot be fetched.

### Troubleshooting (common)
- DNS issues: swap hostnames for IPs from the DB UI.
- Self‑signed TLS on API: set `VERIFY_TLS=false` (or provide `CUSTOM_CA_BUNDLE_PATH`).
- Non‑TLS DBs: set `USE_SSL=false`.
- RediSearch “unknown command”: create the DB with “Search and Query” enabled.
- Roles: if only Admin is present, role substitution is logged and applied automatically.

### Artifacts and Observability
- memtier command saved on the load node: `/tmp/memtier_benchmark.txt`
- Structured JSON logs across scripts for reliable validation
- README contains latest validation outputs and security/TLS handling notes


