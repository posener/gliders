run:
	sudo gunicorn main:app --bind 0.0.0.0:80

run-background:
	sudo gunicorn main:app --bind 0.0.0.0:80 2>log.txt &