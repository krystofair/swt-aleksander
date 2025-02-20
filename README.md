# The Aleksander
Aleksander jest oparty o architekturę usług. Każde przetwarzanie wywołane na konkretnym temacie jest traktowane
jako usługa, jeśli zostało wywołane z zewnątrz. Dlatego w kodzie `clustering.py` jest określenie "internal task",
"internal task" jest wtedy kiedy worker nie może zakończyć swojego zadania bez zakończenia innego więc je opóźnia "delayed".
Wszystkie usługi znajdują się w module `services.py`, z punktu tego modułu jest wywoływany worker,
dlatego to tam istnieje główna aplikacja <b>Celery</b>. Każda usługa tworzy wybrany model danych oraz jest do
niej przypisane wyrażenie regularne, po którym jest wyszukiwana.

## Installation and running
Look to aleksander config, there are configuration for REDIS'es and others.
Create virtual environment for this and `source` it
> source ... | pipenv shell
1. setup postgres database for data
> podman start baxa_test|baxa
2. Run redis-broker for celery and redis-cache for correlations
> podman run --rm -d -p 4601:6379 docker.io/library/redis:8.0-M02-alpine
3. Run aleksander `__main__` app
> python -m aleksander
4. Run some workers of celery for aleksander app
> celery -A aleksander.services:app worker --loglevel=debug
5. Run poiter and start browsing data.
> 

## Dependencies
### Python
* Celery
* Attrs
### Infrastructure
* Redis
* Postgres
