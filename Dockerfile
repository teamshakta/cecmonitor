FROM python:2.7.18-slim-buster

#not sure if this is really needed to copy
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# set work directory
WORKDIR /opt/cecmonitor

# Install adb
RUN apt-get -y update && apt-get -y install adb procps  && apt-get clean && rm -f /var/lib/apt/lists/*_*

# copy the cecmonitor script to the working directory
COPY ./src .

CMD [ "sh", "-c", "python ./cecmonitor.py -i $TV_IP_ADDRESS $ADDITIONAL_ARGS" ]
