# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

LABEL version="23.04.04"

EXPOSE 5000

WORKDIR /src

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
RUN pip install --upgrade pip
COPY requirements.txt /src/requirements.txt
RUN python -m pip install -r requirements.txt
COPY . /src

# Creates a non-root user with an explicit UID and adds permission to access the /src/app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /src
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]