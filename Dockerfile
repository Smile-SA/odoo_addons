FROM odoo:19.0

USER root

COPY ./requirements.txt .
RUN pip3 install --break-system-packages -r ./requirements.txt

RUN apt-get update && \
    apt-get install -y default-jdk

USER odoo
