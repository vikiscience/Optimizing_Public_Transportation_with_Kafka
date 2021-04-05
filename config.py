# urls
BROKER_URL = 'PLAINTEXT://localhost:9092'
DB_URL = 'jdbc:postgresql://postgres:5432/cta'  # 'jdbc:postgresql://localhost:5432/cta'
DB_USER = 'cta_admin'
DB_PW = 'chicago'
SCHEMA_REGISTRY_URL = 'http://localhost:8081'
REST_PROXY_URL = 'http://localhost:8082'  # 'http://rest-proxy:8082'
KAFKA_CONNECT_URL = "http://localhost:8083"
KSQL_URL = "http://localhost:8088"

# topic names
TOPIC_NAME_ARRIVAL = 'com.udacity.arrival'
TOPIC_NAME_STATIONS = 'com.udacity.stations'
TOPIC_NAME_TRANS_STATIONS = 'com.udacity.trans_stations'
TOPIC_NAME_TURNSTILE = 'com.udacity.turnstile'
TOPIC_NAME_TURNSTILE_SUMMARY = 'com.udacity.turnstile_summary'
TOPIC_NAME_WEATHER = 'com.udacity.weather'
