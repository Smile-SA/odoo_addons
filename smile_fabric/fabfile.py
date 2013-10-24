"""Smile automated deployments using Fabric

.. module:: fabfile
   :platform: Debian or Ubuntu
   :synopsis: Fabric to facilitate deployments

.. moduleauthor:: Corentin POUHET-BRUNERIE <corentin.pouhet-brunerie@smile.fr>
"""

import os
import time

from fabric.api import env, local, put, run, task

from fabdecorator import smile_path, smile_secure, smile_settings


def create_branch(version):
    """Create a SVN branch from trunk

    :param version: name of new SVN branch
    :type version: str
    :returns: None
    """
    run('svn cp %(svn_repository)s/trunk %(svn_repository)s/branches/%(version)s '
        '-m "[ADD] Create new branch %(version)s"'
        % {'svn_repository': env.svn_repository, 'version': version})


@smile_path('sources_dir')
def _clean_sources_dir():
    """Delete sources directory

    :returns: None
    """
    run('rm -Rf */')
    run('rm -Rf .svn')
    run('ls | grep tar.gz | xargs rm -f')  # INFO: all files except for *.tar.gz


@smile_path('sources_dir')
def checkout_branch(version):
    """Checkout SVN branch

    :param version: name of SVN branch
    :type version: str
    :returns: None
    """
    _clean_sources_dir()
    run('svn co %(svn_repository)s/branches/%(version)s .'
        % {'svn_repository': env.svn_repository, 'version': version})


@smile_path('sources_dir')
def update_branch(version):
    """Update SVN branch

    :param version: name of SVN branch
    :type version: str
    :returns: None
    """
    run('svn up')


@smile_secure([0, 1])
@smile_path('tag_dir', local=True)
def _clean_tag_dir(tag):
    """Delete tag directory in local

    :param tag: name of SVN tag
    :type tag: str
    :returns: None
    """
    local('rm -Rf %s' % tag)


@smile_path('tag_dir', local=True)
def checkout_tag(tag):
    """Checkout SVN tag in local

    :param tag: name of SVN tag
    :type tag: str
    :returns: None
    """
    local('svn co %(svn_repository)s/tags/%(tag)s %(tag)s'
          % {'svn_repository': env.svn_repository, 'tag': tag})


@smile_path('tag_dir', local=True)
def compress_archive(tag):
    """Compress tag archive

    :param tag: name of SVN tag
    :type tag: str
    :returns: archive filename
    "rtype: str
    """
    archive = "openerp-v%s.tag.gz" % tag
    local('tar -zcvf %s ./%s --exclude-vcs' % (archive, tag))
    return archive


@smile_path('tag_dir', local=True)
def put_archive(archive):
    """Get tag archive

    :param archive: archive filename
    :type archive: str
    :returns: None
    """
    put(archive, env.sources_dir)


@smile_path('sources_dir')
def uncompress_archive(archive):
    """Uncompress tag archive

    :param archive: archive filename
    :type archive: str
    :returns: None
    """
    _clean_sources_dir()
    run('tar -zxvf %s' % archive)


@smile_path('backup_dir')
def dump_database(db_name):
    """Dump database

    :param db_name: name of database
    :type db_name: str
    :returns: backup filename
    :rtype: str
    """
    filename = '%s_%s.dump' % (db_name, time.strftime('%Y%m%d_%H%M%S'))
    run('su postgres -c "pg_dump -f %s -F c -O %s"' % (filename, db_name))
    return os.path.join(env.backup_dir, filename)


@smile_path('backup_dir')
def restore_database(db_name, backup):
    """Restore database

    :param db_name: name of database
    :type db_name: str
    :param backup: backup filename
    :type backup: str
    :returns: None
    """
    run('su postgres -c "pg_restore -v -d %s %s"' % (db_name, backup))


@smile_path('sources_dir')
def upgrade_database(db_name):
    """Upgrade database

    :param db_name: name of database to upgrade
    :type db_name: str
    :returns: None
    """
    run('su openerp -c "openerp-server -c /etc/openerp-server.conf -d %s --load=web,smile_upgrade"' % db_name)


def start_service():
    """Start OpenERP Service

    :returns: None
    """
    run('service openerp-server start')


@smile_secure([0, 1])
def stop_service():
    """Stop OpenERP Service

    :returns: None
    """
    run('service openerp-server stop')


@task
@smile_settings('internal_testing')
def deploy_for_internal_testing(version, db_name, backup=None, do_not_create_branch=False):
    """Deploy in internal testing server

    :param version: name of new SVN branch
    :type version: str
    :param db_name: database name to upgrade
    :type db_name: str
    :param backup: backup filename to restore instead of dump database if is None
    :type backup: str
    :returns: None
    """
    if not do_not_create_branch:
        create_branch(version)
    stop_service()
#     if backup:
#         restore_database(db_name, backup)
#     else:
#         backup = dump_database(db_name)
    checkout_branch(version)
    upgrade_database(db_name)
    start_service()


@task
@smile_settings('customer_testing')
def deploy_for_customer_testing(tag, db_name, backup=None):
    """Deploy in customer testing server

    :param version: name of new SVN branch
    :type version: str
    :param db_name: database name to upgrade
    :type db_name: str
    :param backup: backup filename to restore instead of dump database if is None
    :type backup: str
    :returns: None
    """
    checkout_tag(tag)
    archive = compress_archive(tag)
    put_archive(archive)
    stop_service()
    if backup:
        restore_database(db_name, backup)
    else:
        backup = dump_database(db_name)
    uncompress_archive(archive)
    upgrade_database(db_name)
    start_service()
