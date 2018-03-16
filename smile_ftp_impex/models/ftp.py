# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api
from openerp.exceptions import Warning
from openerp.tools import config
from ftplib import FTP
from os import listdir
from os.path import isfile, join, exists
from os import remove, rename
from optparse import OptionParser
import os
import logging

logging.basicConfig(level=logging.DEBUG)
parser = OptionParser()
parser.add_option("--ftp-host-list", dest="ftp_host_list", default=[], help="""define ftp host list ftp.server.address.com,...""")
parser.add_option("--ftp-port-list", dest="ftp_port_list", default=[21], help="define ftp port list 21,...")
parser.add_option("--ftp-user-list", dest="ftp_user_list", default=['anonymous'], help="define ftp user list anonymous,...")
parser.add_option("--ftp-pswd-list", dest="ftp_pswd_list", default=['anonymous'], help="define ftp password list anonymous,...")
parser.add_option("--ftp-acct-list", dest="ftp_acct_list", default=[], help="define ftp acct list 'accounting information', ...")
parser.add_option("--ftp-timeout-list", dest="ftp_timeout_list", default=[], help="define ftp timeout list 60,...")
parser.add_option("--ftp-path-list", dest="ftp_path_list", default=[],
                  help="used by ftplib cwd, to define ftp server current directory name list ftp_directory_name or /absolute/path/directory/ftp,...")
parser.add_option("--ftp-local-path-list", dest="ftp_local_path_list", default=[],
                  help="define absolut path local directory list where the ftp connection is initialized /absolute/path/directory/local,...")


class FtpImPex(models.TransientModel):
    _name = 'ftp.impex'
    _description = 'Ftp upload download'
    _rec_name = 'id'

    @api.model
    def _connect_ftp(self, ftp_host_row=0, ftp_port_row=0, ftp_user_row=0, ftp_pwd_row=0, ftp_acct_row=0, ftp_timeout_row=0, ftp_dir_name_row=0):
        host = config['ftp_host_list'].split(',')[ftp_host_row]
        port = config.get('ftp_port_list') and int(config['ftp_port_list'].split(',')[ftp_port_row]) or 21
        user = config['ftp_user_list'].split(',')[ftp_user_row]
        pswd = config['ftp_pswd_list'].split(',')[ftp_pwd_row]
        directory = config['ftp_path_list'].split(',')[ftp_dir_name_row]
        acct = config.get('ftp_acct_list') and config['ftp_acct_list'].split(',')[ftp_acct_row]
        timeout = config.get('ftp_timeout_list') and config['ftp_timeout_list'].split(',')[ftp_timeout_row]
        session = FTP()
        if not timeout:
            session.connect(host, port)
        else:
            session = session.connect(host, port, timeout)
        if not acct:
            session.login(user, pswd)
        else:
            session.login(user, pswd, acct)
        session.cwd(directory)
        return session

    @api.model
    def _disconnect_ftp(self, session):
        if session:
            session.close()

    @api.model
    def _get_file_list(self, session):
        return list(set(session.nlst()) - set(list(set([path.split('/')[-1] for path in config['ftp_path_list'].split(',')]))))

    @api.model
    def _destination_local_file_move(self, path_file, dir_file_move, filename):
        if exists(dir_file_move):
            dest_path = join(dir_file_move, filename)
            if exists(dest_path):
                remove(dest_path)
            rename(path_file, dest_path)

    # locally, after an upload file, delete or move files in a directory, can also move files on exception
    # this method can also be used for your future treatments after a download ...
    @api.model
    def _destination_local_file(self, path_file=False, filename=False, del_files=False, move_files=False, move_local_dir_row=0, no_error=True,
                          move_files_on_error=False, move_local_dir_error_row=0):
        if exists(path_file):
            # exception is the master case, if exception and move_files_on_error = False, no move/deletion is done
            if no_error:
                if del_files:
                    remove(path_file)
                elif move_files:
                    self._destination_local_file_move(path_file, config['ftp_local_path_list'].split(',')[move_local_dir_row], filename)
            elif move_files_on_error:
                self._destination_local_file_move(path_file, config['ftp_local_path_list'].split(',')[move_local_dir_error_row], filename)

    @api.model
    def _set_file(self, session, del_files, move_files, path_file, filename, move_local_dir_row, move_files_on_error, move_local_dir_error_row):
        no_error = True
        try:
            with open(path_file, 'rb') as data:
                session.storbinary('STOR ' + filename, data)
        except Exception, e:
            no_error = False
        finally:
            self._destination_local_file(path_file, filename, del_files, move_files, move_local_dir_row, no_error, move_files_on_error,
                                         move_local_dir_error_row)

    @api.model
    def _ftp_set_files(self, session, ftp_local_path_row=0, move_files=False, move_local_dir_row=0, del_files=False, path_file=False,
                       filename=False, move_files_on_error=False, move_local_dir_error_row=0):
        # to export all files inside local directory ftp_local_path_row
        if not (path_file and filename):
            local_dir = config['ftp_local_path_list'].split(',')[ftp_local_path_row]
            for filename in [file_name for file_name in listdir(local_dir) if isfile(join(local_dir, file_name))]:
                path_file = join(local_dir, filename)
                self._set_file(session, del_files, move_files, path_file, filename, move_local_dir_row, move_files_on_error, move_local_dir_error_row)
        # to export only one file generated on the fly by example
        else:
            if isfile(path_file):
                self._set_file(session, del_files, move_files, path_file, filename, move_local_dir_row, move_files_on_error, move_local_dir_error_row)

    @api.model
    def _destination_ftp_file_move(self, session, dir_file_move, ftp_file_name):
        cur_dir = session.pwd()
        session.cwd(dir_file_move)
        path_dest = join(dir_file_move, ftp_file_name)
        if ftp_file_name in self._get_file_list(session):
            session.delete(path_dest)
        session.rename(join(cur_dir, ftp_file_name), path_dest)
        session.cwd(cur_dir)

    @api.model
    def _destination_ftp_file(self, session, del_files=False, move_files=False, ftp_file_name=False, move_ftp_dir_row=0, no_error=True,
                          move_files_on_error=False, move_ftp_dir_error_row=0):
        if no_error:
            if del_files:
                session.delete(path_file)
            elif move_files:
                self._destination_ftp_file_move(session, config['ftp_path_list'].split(',')[move_ftp_dir_row], ftp_file_name)
        elif move_files_on_error:
            self._destination_ftp_file_move(session, config['ftp_path_list'].split(',')[move_ftp_dir_error_row], ftp_file_name)

    @api.model
    def _get_file(self, session, local_dir, del_files, move_files, ftp_file_name, move_ftp_dir_row, move_files_on_error, move_ftp_dir_error_row):
        no_error = True
        try:
            path_file = join(local_dir, ftp_file_name)
            if exists(path_file):
                remove(path_file)
            with open(path_file, 'wb') as data:
                session.retrbinary("RETR " + ftp_file_name, data.write)
        except Exception, e:
            no_error = False
        finally:
            self._destination_ftp_file(session, del_files, move_files, ftp_file_name, move_ftp_dir_row, no_error, move_files_on_error,
                                       move_ftp_dir_error_row)

    @api.model
    def _ftp_get_files(self, session, ftp_local_path_row=0, move_files=False, move_ftp_dir_row=0, del_files=False, ftp_file_name=False,
                       move_files_on_error=False, move_ftp_dir_error_row=0):
        local_dir = config['ftp_local_path_list'].split(',')[ftp_local_path_row]
        if not ftp_file_name:
            for ftp_file_name in self._get_file_list(session):
                self._get_file(session, local_dir, del_files, move_files, ftp_file_name, move_ftp_dir_row, move_files_on_error,
                               move_ftp_dir_error_row)
        else:
            self._get_file(session, local_dir, del_files, move_files, ftp_file_name, move_ftp_dir_row, move_files_on_error, move_ftp_dir_error_row)
