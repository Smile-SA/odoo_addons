The module must be loaded as a server-wide module. Otherwise its code is loaded too late
and no upgrade runs at startup.

Start the server with:

``` shell
odoo-bin -c <config_file> -d <db_name> --load=web,smile_upgrade
```

or add this line to the Odoo configuration file:

``` ini
server_wide_modules = web,smile_upgrade
```
