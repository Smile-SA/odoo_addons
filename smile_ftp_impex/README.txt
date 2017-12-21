1) define odoo config file parameters comma separated without space:

ftp_host_list = ftp.server.address.com,...
ftp_port_list = 21, ... # default value
ftp_user_list = anonymous, ... # default_value
ftp_pswd_list = anonymous, ... # default_value
ftp_acct_list = # optional
ftp_timeout_list = # optional
ftp_path_list = /absolute/path/directory/ftp,...
ftp_local_path_list = /absolute/path/directory/local,...

2) UPload file, create a method like this:

class MyClass(models.Model):
    _name = 'my.class'


    @api.one
    def _upload_files(self):
        impex = self.env['ftp.impex']
        try:
            # if you just have one element for a config parameter, do not use this parameter in body method,
            # just verify if default value is correct for your need

            # ftp_host_row=0 first element in list of config file parameter ftp_path_list
            # ftp_port_row=0 first element in list of config file parameter ftp_port_list
            # ftp_user_row=0 first element in list of config file parameter ftp_user_list
            # ftp_pwd_row=0 first element in list of config file parameter ftp_pswd_list
            # ftp_acct_row=0 first element in list of config file parameter ftp_acct_list
            # ftp_timeout_row=0 first element in list of config file parameter ftp_timeout_list
            # ftp_dir_name_row=0 first element in list of config file parameter ftp_path_list
            
            session = impex._connect_ftp(ftp_host_row=0, ftp_port_row=0, ftp_user_row=0, ftp_pwd_row=0, ftp_acct_row=0, ftp_timeout_row=0,
                                         ftp_dir_name_row=0)

            # ftp_local_path_row=0 first element in list of config file parameter ftp_local_path_list
            # move_files boolean to move file or not after upload by example in a directory named ok
            # move_local_dir_row=0 first element in list of config file parameter ftp_local_path_list if move_files=True
            # del_files boolean remove file or not after upload
            # path_file is absolut path of the directory containing files
            # filename is the name of a unique file if there is only one file to upload, by example a file created on the fly in temp dir,
            # if False, directory is scanned to get list of all files name
            # move_files_on_error boolean, if True, in case of error in your upload, you can move the file in a directory named error
            # move_local_dir_error_row=0 first element in list of config file parameter ftp_local_path_list if move_files_on_error=True

            # for file movement after upload, test cases are in this order: if no error at upload first verify if file must be deleted locally,
            # secondly if move_files=True file is moved to move_local_dir_row; but if error and move_files_on_error=True file is locally moved
            # in move_local_dir_error_row

            impex._ftp_set_files(self, session, ftp_local_path_row=0, move_files=False, move_local_dir_row=0, del_files=False,
                                 path_file=False, filename=False, move_files_on_error=False, move_local_dir_error_row=0)
            if impex and session:
                impex._disconnect_ftp(session)
        except Exception, e:
            print '%s' % e

3) Dowload file, create a method like this:


class MyClass(models.Model):
    _name = 'my.class'

    @api.one
    def _download_files(self):
        impex = self.env['ftp.impex']
        try:
            # if you just have one element for a config parameter, do not use this parameter in body method,
            # just verify if default value is correct for your need

            # ftp_host_row=0 first element in list of config file parameter ftp_path_list
            # ftp_port_row=0 first element in list of config file parameter ftp_port_list
            # ftp_user_row=0 first element in list of config file parameter ftp_user_list
            # ftp_pwd_row=0 first element in list of config file parameter ftp_pswd_list
            # ftp_acct_row=0 first element in list of config file parameter ftp_acct_list
            # ftp_timeout_row=0 first element in list of config file parameter ftp_timeout_list
            # ftp_dir_name_row=0 first element in list of config file parameter ftp_path_list
            
            session = impex._connect_ftp(ftp_host_row=0, ftp_port_row=0, ftp_user_row=0, ftp_pwd_row=0, ftp_acct_row=0, ftp_timeout_row=0,
                                         ftp_dir_name_row=0)

            # ftp_local_path_row=0 first element in list of config file parameter ftp_local_path_list
            # move_files boolean to move file or not after upload by example in a directory named ok
            # move_ftp_dir_row=0 first element in list of config file parameter ftp_path_list if move_files=True
            # del_files boolean remove file or not after upload
            # path_file is absolut path of the directory containing files
            # ftp_file_name is the name of a unique file if there is only one file to upload, by example a file created on the fly in temp dir,
            # if False, directory is scanned to get list of all files name
            # move_files_on_error boolean, if True, in case of error in your upload, you can move the file in a directory named error
            # move_local_dir_error_row=0 first element in list of config file parameter ftp_local_path_list if move_files_on_error=True

            # for file movement after upload, test cases are in this order: if no error at upload first verify if file must be deleted locally,
            # secondly if move_files=True file is moved to move_local_dir_row; but if error and move_files_on_error=True file is locally moved
            # in move_local_dir_error_row

            impex._ftp_get_files(self, session, ftp_local_path_row=0, move_files=False, move_ftp_dir_row=0, del_files=False,
                                 ftp_file_name=False, move_files_on_error=False, move_ftp_dir_error_row=0)
            if impex and session:
                impex._disconnect_ftp(session)
        except Exception, e:
            print '%s' % e
