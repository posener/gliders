run:
	FLASK_APP=main.py ./venv/bin/flask run --host 0.0.0.0 --port 80

debug:
	FLASK_DEBUG=1 FLASK_APP=main.py ./venv/bin/flask run
