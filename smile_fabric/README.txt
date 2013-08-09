Smile automated deployments using Fabric
========================================
  
Tasks
-----

deploy_for_internal_testing
    Deploy in internal testing server

    :param version: name of new SVN branch
    :type version: str
    :param db_name: database name to upgrade
    :type db_name: str
    :param backup: backup filename to restore instead of dump database if is None
    :type backup: str
    :returns: None

deploy_for_customer_testing
    Deploy in customer testing server

    :param version: name of new SVN branch
    :type version: str
    :param db_name: database name to upgrade
    :type db_name: str
    :param backup: backup filename to restore instead of dump database if is None
    :type backup: str
    :returns: None

Configuration
-------------

Take example from smile_fabric/.fabrirc

Suggestions & Feedback
----------------------
corentin.pouhet-brunerie@smile.fr
