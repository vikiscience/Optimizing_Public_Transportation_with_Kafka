# Public Transit Status with Apache Kafka

In this project, a streaming event pipeline is constructed around Apache Kafka and its ecosystem. Using public data from the [Chicago Transit Authority](https://www.transitchicago.com/data/) (**CTA**) we will construct an event pipeline around Kafka that allows us to simulate and display the status of train lines in real time.

In the end, you will be able to monitor a website to watch trains move from station to station.

![Final User Interface](images/ui.png)


## Prerequisites

The following are required to complete this project:

* Docker
* Python 3.7
* Access to a computer with a minimum of 16gb+ RAM and a 4-core CPU to execute the simulation
* P.S.: make sure your docker has enough memory too!

## Install project requirements

```bash
conda create -n streaming python=3.7
conda activate streaming
pip install -r requirements_all.txt
```

## Description

The goal of this project is to develop a dashboard for CTA displaying system status for its commuters. We have decided to use Kafka and ecosystem tools like REST Proxy and Kafka Connect to accomplish this task.

Our architecture will look like so:

![Project Architecture](images/diagram.png)

### Step 1: Create Kafka Producers

The first step in our plan is to configure the train stations to emit some of the events that we need. The CTA has placed a sensor on each side of every train station that can be programmed to take an action whenever a train arrives at the station.

It is accomplished as follows:

1. Every Kafka producer inherits from a Producer class found in `producers/models/producer.py`
1. All events of train arrivals are defined by a `value` schema in `producers/models/schemas/arrival_value.json` with the following attributes:
	* `station_id`
	* `train_id`
	* `direction`
	* `line`
	* `train_status`
	* `prev_station_id`
	* `prev_direction`
1. Station class in `producers/models/station.py` is responsible that:
	* A Kafka topic is created for all stations to track the arrival events
	* The station emits an `arrival` event to Kafka whenever the `Station.run()` function is called
	* Events emitted to Kafka are paired with the Avro `key` and `value` schemas
1. All turnstile events are defined by a `value` schema in `producers/models/schemas/turnstile_value.json` with the following attributes:
	* `station_id`
	* `station_name`
	* `line`
1. Turnstile class in `producers/models/turnstile.py` is responsible that:
	* A Kafka topic is created for each turnstile for each station to track the turnstile events
	* The station emits a `turnstile` event to Kafka whenever the `Turnstile.run()` function is called
	* Events emitted to Kafka are paired with the Avro `key` and `value` schemas
1. You can open the [Landoop Schema Registry UI](http://localhost:8086) and [Landoop Kafka Topics UI](http://localhost:8085) in browser to check the status of the schemas and the contents of all topics.


### Step 2: Configure Kafka REST Proxy Producer

Additionally, we also send weather readings into Kafka from a weather hardware. Let us assume, that this hardware is old and we cannot use the Python Client Library due to hardware restrictions. Instead, we are going to use HTTP REST to send the data to Kafka from the hardware using Kafka's REST Proxy.

It is accomplished as follows:

1. All weather events are defined by a `value` schema in `producers/models/schemas/weather_value.json` with the following attributes:
	* `temperature`
	* `status`
1. Weather class in `producers/models/weather.py` is responsible that:
	* A Kafka topic is created for weather events
	* The weather model emits `weather` event to Kafka REST Proxy whenever the `Weather.run()` function is called
	* Events emitted to REST Proxy are paired with the Avro `key` and `value` schemas


### Step 3: Configure Kafka Connect

Finally, we need to extract station information from a PostgreSQL database into Kafka. We've decided to use the [Kafka JDBC Source Connector](https://docs.confluent.io/current/connect/kafka-connect-jdbc/source-connector/index.html).

It is accomplished as follows:

1. Complete the code and configuration in `producers/connectors.py`:
	* You can run this file directly to test your connector, rather than running the entire simulation
	* You can open the [Landoop Kafka Connect UI](http://localhost:8084) and [Landoop Kafka Topics UI](http://localhost:8085) in browser to check the status and output of the Connector
	* To delete a misconfigured connector: `CURL -X DELETE localhost:8083/connectors/jdbc_source_stations`


### Step 4: Configure the Faust Stream Processor

We will leverage Faust Stream Processing to transform the raw Stations table that we ingested from Kafka Connect. The raw format from the database has more data than we need, and the line color information is not conveniently configured. To remediate this, we're going to ingest data from our Kafka Connect topic, and transform the data.

It is accomplished in `consumers/faust_stream.py`, and you must run this script with the following command:

`python -m faust -A consumers.faust_stream worker -l info`


### Step 5: Configure the KSQL Table

Next, we will use KSQL to aggregate turnstile data for each of our stations. Recall that when we produced turnstile data, we simply emitted an event, not a count. What would make this data more useful would be to summarize it by station so that downstream applications always have an up-to-date count.

It is accomplished in `consumers/ksql.py`, and you can run this script separately.


### Step 6: Create Kafka Consumers

With all the required data in Kafka, our final task is to consume the data in the web server that is going to serve the transit status pages to our commuters.

It is accomplished as follows:

1. Every Kafka consumer inherits from the Consumer class found in `consumers/consumer.py`
1. Line class in `consumers/models/line.py` is responsible for handling messages from Arrival, Stations and Turnstile summary topics.
1. Lines class in `consumers/models/lines.py` contains 3 lines of CTA ("red", "green" and "blue", seen on the resulting website) and dispatches the messages to one particular line or all lines in a row, depending on the message's topic.
1. Weather class in `consumers/models/weather.py` reads weather from a corresponding topic and is used to show the info at the top-right corner of the website.


### Documentation

Please also refer to the examples and documentation below:

* [Confluent Python Client Documentation](https://docs.confluent.io/current/clients/confluent-kafka-python/#)
* [Confluent Python Client Usage and Examples](https://github.com/confluentinc/confluent-kafka-python#usage)
* [REST Proxy API Reference](https://docs.confluent.io/current/kafka-rest/api.html#post--topics-(string-topic_name))
* [Kafka Connect JDBC Source Connector Configuration Options](https://docs.confluent.io/current/connect/kafka-connect-jdbc/source-connector/source_config_options.html)
* [Python Faust Library Documentation](https://faust.readthedocs.io/en/latest/)


## Directory Layout

The project consists of two main directories, `producers` and `consumers`.

The following directory layout indicates the files with `*`, if they were modified by the project owner.

```
├── config.py *
├── consumers
│   ├── consumer.py *
│   ├── faust_stream.py *
│   ├── ksql.py *
│   ├── models
│   │   ├── lines.py *
│   │   ├── line.py *
│   │   ├── station.py *
│   │   └── weather.py *
│   ├── requirements.txt
│   ├── server.py
│   ├── topic_check.py
│   └── templates
│       └── status.html
└── producers
    ├── connector.py *
    ├── models
    │   ├── line.py
    │   ├── producer.py *
    │   ├── schemas
    │   │   ├── arrival_key.json
    │   │   ├── arrival_value.json *
    │   │   ├── turnstile_key.json
    │   │   ├── turnstile_value.json *
    │   │   ├── weather_key.json
    │   │   └── weather_value.json *
    │   ├── station.py *
    │   ├── train.py
    │   ├── turnstile.py *
    │   ├── turnstile_hardware.py
    │   └── weather.py *
    ├── requirements.txt
    └── simulation.py
```

## Running and Testing

To run the simulation, you must first start up the Kafka ecosystem on your machine utilizing Docker Compose.

```%> docker-compose up```

Docker compose will take a 3-5 minutes to start, depending on your hardware. Please be patient and wait for the docker-compose logs to slow down or stop before beginning the simulation.

Once docker-compose is ready, the following services will be available:

| Service | Host URL | Docker URL |
| --- | --- | --- |
| Public Transit Status | [http://localhost:8888](http://localhost:8888) | n/a | ||
| Landoop Kafka Connect UI | [http://localhost:8084](http://localhost:8084) | http://connect-ui:8084 |
| Landoop Kafka Topics UI | [http://localhost:8085](http://localhost:8085) | http://topics-ui:8085 |
| Landoop Schema Registry UI | [http://localhost:8086](http://localhost:8086) | http://schema-registry-ui:8086 |
| Kafka | PLAINTEXT://localhost:9092 <br> PLAINTEXT://localhost:9093 <br> PLAINTEXT://localhost:9094 | PLAINTEXT://kafka0:9092 <br> PLAINTEXT://kafka1:9093 <br> PLAINTEXT://kafka2:9094 |
| REST Proxy | [http://localhost:8082](http://localhost:8082/) | http://rest-proxy:8082/ |
| Schema Registry | [http://localhost:8081](http://localhost:8081/ ) | http://schema-registry:8081/ |
| Kafka Connect | [http://localhost:8083](http://localhost:8083) | http://kafka-connect:8083 |
| KSQL | [http://localhost:8088](http://localhost:8088) | http://ksql:8088 |
| PostgreSQL | `jdbc:postgresql://localhost:5432/cta` | `jdbc:postgresql://postgres:5432/cta` <br> (username: `cta_admin`, password: `chicago`) |


### Running the Simulation

There are two pieces to the simulation, the `producer` and `consumer`. 
For testing purposes, you may run each piece of the project separately. 
However, in order to verify the end-to-end system, it is critical that you run them at the same time (`producer` and `consumer` in 2 different terminals). 
Note that the table creation done by Faust application and KSQL script needs to be run (at least) once.

#### (Optional) Check the Postgresql DB:

Open the terminal inside a Postgres container:

1. `psql -h postgres -U cta_admin -d cta` (and enter the db password)

2. Explore the tables:

```bash
select * from stations;
\d stations;
```

#### Run the `producer`:

`python -m producers.simulation`

Once the simulation is running, you may hit `Ctrl+C` at any time to exit.


#### Run the Faust Stream Processing Application:

`python -m faust -A consumers.faust_stream worker -l info`


#### Run the KSQL Creation Script:

`python -m consumers.ksql`


#### (Optional) Check the KSQL DB:

Open the terminal inside a KSQL server container:

1. `ksql`
2. Explore the tables:

```bash
ksql
SHOW TOPICS;
SHOW TABLES;
SHOW QUERIES;
DESCRIBE <table_name>;
SELECT * FROM <table_name>;
TERMINATE <query_name>;
DROP TABLE <table_name>;
```

#### Run the `consumer`:

`python -m consumers.server`

Once the server is running, you can watch the [website](http://localhost:8888), and exit by hitting `Ctrl+C` at any time.
