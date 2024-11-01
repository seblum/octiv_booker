# Use Python 3.10 as the base image
FROM python:3.11

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# Set the timezone to Europe/Berlin
RUN apt update && apt install tzdata -y
ENV TZ="Europe/Berlin"

# Install Chromedriver
RUN apt-get install -yqq unzip
ENV ChromedriverVersion="130.0.6723.91"
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/$ChromedriverVersion/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /usr/local/bin/

# Set the display port to avoid crashes
ENV DISPLAY=:99

# Define build-time arguments to pass credentials and configuration
ARG IS_TEST=${IS_TEST:-""}
ARG OCTIV_USERNAME=${OCTIV_USERNAME:-""}
ARG OCTIV_PASSWORD=${OCTIV_PASSWORD:-""}
ARG EMAIL_SENDER=${EMAIL_SENDER:-""}
ARG EMAIL_PASSWORD=${EMAIL_PASSWORD:-""}
ARG EMAIL_RECEIVER=${EMAIL_RECEIVER:-""}
ARG DAYS_BEFORE_BOOKABLE=${DAYS_BEFORE_BOOKABLE:-""}
ARG EXECUTION_BOOKING_TIME=${EXECUTION_BOOKING_TIME:-""}

# Set environment variables for the application
ENV OCTIV_USERNAME=${OCTIV_USERNAME}
ENV OCTIV_PASSWORD=${OCTIV_PASSWORD}
ENV EMAIL_SENDER=${EMAIL_SENDER}
ENV EMAIL_PASSWORD=${EMAIL_PASSWORD}
ENV EMAIL_RECEIVER=${EMAIL_RECEIVER}
ENV DAYS_BEFORE_BOOKABLE=${DAYS_BEFORE_BOOKABLE}
ENV EXECUTION_BOOKING_TIME=${EXECUTION_BOOKING_TIME}

# Create a directory for the application
RUN mkdir /app
# Copy the Python application files into the container
COPY ./src /app/src
COPY ./pyproject.toml /app

WORKDIR /app

# Set PYTHONPATH to include the current working directory
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

# Install Poetry for managing dependencies
RUN pip3 install poetry
# Configure Poetry to not create a virtual environment and install dependencies
RUN poetry config virtualenvs.create false && poetry install

# Set the entrypoint command to run the application with Poetry
ENTRYPOINT [ "poetry", "run", "slotBooker" ]
