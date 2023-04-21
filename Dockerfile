# first stage
FROM python:2.7.18-slim-buster
COPY requirements.txt .

# install dependencies to the local user directory (eg. /root/.local)
RUN pip install -r requirements.txt

# second unnamed stage
WORKDIR /opt/cecmonitor

# Install git, ssh and mariadb-dev
RUN apt-get -y update && apt-get -y install adb procps  && apt-get clean && rm -f /var/lib/apt/lists/*_*

# copy only the dependencies installation from the 1st stage image
COPY ./src .

CMD [ "sh", "-c", "python ./cecmonitor.py -i $TV_IP_ADDRESS $ADDITIONAL_ARGS" ]
