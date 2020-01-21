FROM python:3.7.0-slim
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

ADD veracode/veracode-cli.py /veracode/veracode-cli.py
ADD requirements.txt /veracode/requirements.txt
ADD veracode/helpers/* /veracode/helpers/
ADD veracode/services/* /veracode/services/
ADD debug.sh /veracode/bin/debug.sh
RUN ["chmod", "+x", "/veracode/bin/debug.sh"]
ADD veracode-cli /veracode/bin/veracode-cli
RUN ["chmod", "+x", "/veracode/bin/veracode-cli"]
ADD gitlab-veracode-cli /veracode/bin/gitlab-veracode-cli
RUN ["chmod", "+x", "/veracode/bin/gitlab-veracode-cli"]

RUN pip install -r veracode/requirements.txt

CMD [ "python", "/veracode/veracode-cli.py" ]