===================
Smile Multi Website
===================

This module add a menu to configure several website.
Multi-site work without it but it is more user friendly


Local Configuration
===================

If you want test the multi-site you have to use apache2 (or nginx).
Here is a little tutorial:

- install apache

sudo apt-get install apache2

* create your first site redirection

cd /etc/apache2/sites-available/

sudo nano odoo1.conf ::

    <VirtualHost *:80>
        ServerName odoo1.fr
        ServerAlias www.odoo1.fr

        ErrorLog ${APACHE_LOG_DIR}/odoo.error.log
        CustomLog ${APACHE_LOG_DIR}/odoo.access.log combined
        LogLevel warn

        ProxyRequests Off
        <Proxy *>
            Order deny,allow
            Allow from all
        </Proxy>

        ProxyPass / http://127.0.0.1:8069/
        ProxyPassReverse / http://127.0.0.1:8069/

        <Location />
            Order allow,deny
            Allow from all
        </Location>

    </VirtualHost>

* create your second site redirection

sudo nano odoo2.conf ::

    <VirtualHost *:80>
        ServerName odoo2.fr
        ServerAlias www.odoo2.fr

        ErrorLog ${APACHE_LOG_DIR}/odoo.error.log
        CustomLog ${APACHE_LOG_DIR}/odoo.access.log combined
        LogLevel warn

        ProxyRequests Off
        <Proxy *>
            Order deny,allow
            Allow from all
        </Proxy>

        ProxyPass / http://127.0.0.1:8069/
        ProxyPassReverse / http://127.0.0.1:8069/

        <Location />
            Order allow,deny
            Allow from all
        </Location>

    </VirtualHost>

- Add your configuration file on the site enable and restart apache

sudo a2ensite odoo1.conf

sudo a2ensite odoo2.conf

sudo service apache2 restart

- Add your domain on the hosts file

sudo nano /etc/hosts ::

    127.0.0.1       localhost
    127.0.0.1       odoo1.fr
    127.0.0.1       odoo2.fr

Usage
=====

Connect odoo on localhost:8069 and install the module

On the new website menu (Website/configuration/website) create two site and put your respective domain on the "domain" value.

On the page menu (hidden by default, go to dev mode), edit the Home page.

On the website list, add the localhost website if you want a unique home page for all website

Try to connect on odoo1.fr, odoo will signal that no page exist.

Just click on create page, it will not be visible for your other website.