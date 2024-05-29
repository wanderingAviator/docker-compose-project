FROM python:3.11.9
WORKDIR /app
RUN pip install flask sqlalchemy flask_sqlalchemy flask_login
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host", "0.0.0.0"]