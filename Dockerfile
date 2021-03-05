FROM odoo:13.0

USER root

COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt

USER odoo
