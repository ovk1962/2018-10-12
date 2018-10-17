#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pr_file_FTP_09-10-2018.py
#
import os
import sys
if sys.version_info[0] >= 3:
    import PySimpleGUI as sg
else:
    import PySimpleGUI27 as sg
import time
import ftplib
import logging

#=======================================================================
def upload_ftp_file():
    """ To copy file_www_A7 into fin2016.far.ru by FTP               """
    server_www ='fin2016.far.ru'
    username_www = 'w501038'
    password_www = 'htku6a74'
    ftpPath_www = '//public_html//'
    path_dir  = 'D://'
    path_www_name = 'file_www_A7.txt'
    try:
        ftp = ftplib.FTP(server_www, timeout = 5)
        ftp.login(username_www, password_www)
        ftp.cwd(ftpPath_www)
        ftp.set_pasv(True)
        os.chdir(path_dir)
        with open(path_www_name,'r+b') as myfile:
            ftp.storbinary('STOR '+path_www_name, myfile)
            #print(ftp.stat_result)
            #print(dir(ftp))
            ftp.close
        #print ('successfully sent file to FTP')
    except Exception as ex:
        err_msg = 'upload_ftp_file => ' + str(ex)
        print(err_msg)
        return [1, err_msg]
    finally:
        pass
    return [0, 'OK']
#=======================================================================
class Class_LOGGER():
    def __init__(self):
        #self.logger = logging.getLogger(__name__)
        self.logger = logging.getLogger('__main__')
        self.logger.setLevel(logging.INFO)
        # create a file handler
        self.handler = logging.FileHandler('_logger_FTP.log')
        self.handler.setLevel(logging.INFO)
        # create a logging format
        #self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        # add the handlers to the logger
        self.logger.addHandler(self.handler)

    def wr_log_info(self, msg):
        self.logger.info(msg)

    def wr_log_error(self, msg):
        self.logger.error(msg)
#=======================================================================

def main():
    log  = Class_LOGGER()
    log.wr_log_info('*** START ***')
    txt_clock = sg.Text('Send file by FTP every 1 minute ', key='txt_clock')
    layout = [[txt_clock],
              [sg.ProgressBar(60, orientation='h', size=(20,1), key='progress')],
              [sg.Cancel()]]
    window = sg.Window('Send file by FTP hh.mm.11 sec ').Layout(layout)
    progress_bar = window.FindElement('progress')
    tm_s = 0
    while True:
        button, values = window.ReadNonBlocking()
        if button == 'Cancel' or values == None:
            break
        if tm_s != time.localtime().tm_sec:
            tm_s = time.localtime().tm_sec
            txt_frmt = "%d.%m.%Y   %H:%M:%S"
            txt_clock.Update(time.strftime(txt_frmt, time.localtime()))
            progress_bar.UpdateBar(tm_s+1)
            if tm_s == 7:
                #--- check file cntr.file_path_DATA ------------
                if not os.path.isfile('D://file_www_A7.txt'):
                    err_msg = 'can not find file'
                    log.wr_log_error(err_msg)
                    print(err_msg)
                else:
                    #--- send file by FTP ----------------------
                    rq = upload_ftp_file()
                    if rq[0] != 0:
                        log.wr_log_error(rq[1])
                        txt_clock.Update('ERROR file send FTP')
                    else:
                        txt_clock.Update('D://file_www_A7.txt send FTP')
        time.sleep(0.2)
    window.CloseNonBlocking()
    log.wr_log_info('*** FINISH ***')
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
