Add these options to the Odoo configuration file:

- `upgrades_path` (required): path to the upgrades directory.
- `stop_after_upgrades`: stop the server once the upgrades are applied (exit code 0), or
  when they fail (exit code 1). Nothing stops if there was no upgrade to apply.
- `no_upgrade_lock`: do not take the database lock while upgrading.
- `force_reload_upgrade`: apply the upgrade of the current code version again, even if
  the database already has it. It can also be set in `upgrade.conf`.

The last three options are read as raw text from the Odoo configuration file: any value,
`False` included, turns them on. To keep one off, leave it out of the file.

Structure the upgrades directory like this:

``` text
project
└── upgrades
    ├── 1.1
    │   ├── __upgrade__.py
    │   ├── *.sql
    │   ├── *.py   # post-load only
    │   ├── *.csv  # post-load only
    │   └── *.xml  # post-load only
    ├── 1.2
    │   ├── __upgrade__.py
    │   └── *.sql
    └── upgrade.conf
```

`upgrade.conf` sets the version of the code. Only the `[options]` section is read:

``` ini
[options]
version=1.2
```

Each `__upgrade__.py` holds a Python dictionary with these keys:

- `version`: version of the upgrade.
- `databases`: names of the databases the upgrade applies to. Leave it empty to apply
  it to all databases.
- `description`: free text.
- `modules_to_upgrade`: modules to update, or to install if they are not installed yet.
- `modules_to_install_at_creation`: modules to install when the database is created.
- `translations_to_reload`: language codes to reload after the upgrade.
- `pre-load`: `.sql` files run before the modules are loaded.
- `post-load`: `.sql`, `.py`, `.csv` and `.xml` files run after the modules are loaded.

File paths are relative to the upgrade folder. Each Python file in `post-load` must
define a `post_load_hook(env)` function.

Example:

``` python
{
    "version": "1.2",
    "databases": [],
    "description": "New pricelists",
    "modules_to_upgrade": ["my_module"],
    "modules_to_install_at_creation": ["my_module"],
    "translations_to_reload": ["fr_FR"],
    "pre-load": ["rename_columns.sql"],
    "post-load": [
        "update_partners.sql",
        ("fix_product_pricelist.py", "rollback_and_continue"),
    ],
}
```

As in this example, a `post-load` entry can be a tuple that sets how errors are handled
for that file:

- `raise` (default): stop the upgrade and raise the error.
- `rollback_and_continue`: undo what the file did and go on with the next files.
- `not_rollback_and_continue`: keep what the file did and go on with the next files.
