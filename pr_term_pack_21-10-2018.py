#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pr_term_pack_21-10-2018.py
#
#=======================================================================
import os
import sys
import math
import time
import logging
import smtplib
import sqlite3
from datetime import datetime
from datetime import timezone
import PySimpleGUI as sg
#1======================================================================
# TO DO  add name DATA file in GUI
#=======================================================================
menu_def = [['SQL', ['merge hist to archiv','convert sql txt','table HIST empty']],
            ['Calc', ['Calc archiv_pack', 'Calc pack_today'],],
            ['Test', ['Test SQL',  ['SQL tbl DATA', 'SQL tbls TODAY & ARCHIV', ],],],
            ['Test WWW', 'File WWW'],
            ['Help', 'About...'],
            ['Exit', 'Exit']
            ]
sg_txt = [  sg.T('-9999.99',  font='Helvetica 40'),
            sg.Multiline(default_text='String 01\nString 02\nString 03\nString 04\nString 05',
                size=(50, 5), autoscroll=True),
            sg.T('00.00.0000    00:00:00',  font='Helvetica 8')
            ]

file_path_DATA  = 'D:\\str_log_ad_A7.txt'
file_path_WWW   = 'D:\\file_www_A7.txt'
dirr = os.path.abspath(os.curdir)
db_path_FUT     = dirr + '\\' + 'FUT_today.sqlite'
db_path_FUT_arc = dirr + '\\' + 'FUT_archiv.sqlite'
name_trm = 'TRM_1.21_AD_A7'
#=======================================================================
def main():
    #-------------------------------------------------------------------
    # Display data in a table format
    #-------------------------------------------------------------------
    sg.SetOptions(element_padding=(0,0))

    layout = [ [sg.Menu(menu_def, tearoff=False)],
               [sg_txt[0]],  [sg_txt[1]], [sg_txt[2]] ]  #, [sg_txt[2]], [sg_txt[3]], [sg_txt[4]], [sg_txt[5]]]

    form = sg.FlexForm(name_trm, return_keyboard_events=True, grab_anywhere=False, use_default_focus=False)
    form.Layout(layout)

    len_hist_fut = sec_num = sec_3num = sec_16num = sec_59num = 0
    stroki = ['','','','','']
    values = []
    button = ''
    #-------------------------------------------------------------------
    # init CONTR
    #-------------------------------------------------------------------
    cntr = Class_CONTR(file_path_DATA,
                        db_path_FUT,
                        db_path_FUT_arc)
    rq = init_cntr(cntr)
    init_cntr_ok = True
    if rq[0] != 0:
        sg.Popup('Error init_cntr!', rq[1])
        init_cntr_ok = False
    # main cycle   -----------------------------------------------------
    while True:
        buf_multiline = ''
        button, values = form.ReadNonBlocking()
        if button == 'Exit':  break
        menu_buttons(cntr, button)

        if init_cntr_ok:
            tm_s = time.localtime().tm_sec
            tm_m = time.localtime().tm_min
            if ( ((tm_s % 1) == 0) and (tm_s != 0) ):
                if (sec_num != tm_s ):
                    sec_num = tm_s
                    txt_frmt = "%H:%M:%S   %d.%m.%Y"
                    buf_txt_status = time.strftime(txt_frmt, time.localtime())
                    sg_txt[2].Update(buf_txt_status)
                    sg_txt[0].Update(cntr.term.account.acc_profit)

                    if ((tm_s % 3) == 0):                       # 3 seconds period
                        buf_txt_status = time.strftime("%H.%M.%S ", time.localtime())
                        rq = cntr.term.rd_term()
                        stroki[0] = buf_txt_status + ' read_term ____ ' + rq[1] + '\n'
                        #
                        # parse DATA file
                        if rq[0] == 0:
                            rq = cntr.term.parse_str_in_file()
                            #
                            # rewrite table DATA
                            if rq[0] == 0:
                                sg_txt[0].Update(cntr.term.account.acc_profit)
                                duf_list = []
                                for j, jtem in enumerate(cntr.term.str_in_file):
                                    buf = (jtem,)
                                    duf_list.append(buf)
                                req = cntr.db_FUT_data.rewrite_table('data', duf_list, val = '(?)')
                                stroki[1] = buf_txt_status + ' rewrite_table_____' + req[1] + '\n'
                                #
                                # prepair string for table HIST_TODAY
                                if req[0] != 0:
                                    err_msg = 'rewrite_table(_data_) ' + rq[1]
                                    cntr.log.wr_log_error(err_msg)
                                req = cntr.term.prpr_str_hist()
                                stroki[2] = buf_txt_status + ' prepare_str_hist____' + rq[1] + '\n'
                                #
                                # add new string to table HIST_TODAY
                                if req[0] == 0:
                                    buf_s = (cntr.term.dt_data, cntr.term.str_for_hist)
                                    duf_list = []
                                    duf_list.append(buf_s)
                                    req = cntr.db_FUT_data.write_table_db('hist_today', duf_list)
                                    stroki[3] = buf_txt_status + ' write_hist_DB____' + req[1] + '\n'
                                    if req[0] != 0:
                                        err_msg = 'write_table_db(_hist_today_) ' + rq[1]
                                        cntr.log.wr_log_error(err_msg)
                                else:
                                    err_msg = 'cntr.term.prepare_str_hist' + req[1]
                                    cntr.log.wr_log_error(err_msg)
                            else:
                                err_msg = 'cntr.term.parse_str_in_file' + rq[1]
                                cntr.log.wr_log_error(err_msg)
                        else:
                            stroki[1] = '  ' + cntr.term.path_trm + '\n'
                            stroki[2] = '\n'
                            stroki[3] = '\n'

                    if ((tm_s % 16) == 0):
                        rq  = cntr.db_FUT_data.get_table_db_with('hist_today')
                        if rq[0] == 0:
                            arr_hist_today = rq[1]
                            if len(arr_hist_today) != 0:
                                # convert from arr_hist_today 15 sec to cntr.hist_fut 60 sec
                                cntr.hist_fut = []
                                last_ind_sec = 0
                                for item in arr_hist_today:
                                    if (item[0] - last_ind_sec) > 59:
                                        last_ind_sec = item[0]
                                        cntr.hist_fut.append(item)
                                if len_hist_fut != len(cntr.hist_fut):
                                    len_hist_fut = len(cntr.hist_fut)
                                    # calc from cntr.hist_fut  to  cntr.mdl[i_mdl].archiv_pack_today
                                    calc_today_packets(cntr)
                                    name_list = []
                                    name_list = prepair_today_pack(cntr)
                                    # rewrite to SQL table  pack_today / cntr.db_FUT_data.rewrite_table('pack_today', name_list))
                                    rq  = cntr.db_FUT_data.rewrite_table('pack_today', name_list)
                                    if rq[0] != 0:
                                        err_msg = 'rewrite_table_arc pack_today' + rq[1]
                                        cntr.log.wr_log_error(err_msg)
                                    stroki[4]  = 3*'_' + cntr.hist_fut[0][1].split('|')[0]
                                    stroki[4] += 3*'_' + cntr.hist_fut[-1][1].split('|')[0]
                                    stroki[4] += 3*'_' + str(len(cntr.hist_fut)) +  3*'_'
                            else:
                                stroki[4]  = 'hist is EMPTY'
                        else:
                            err_msg = 'ERROR - can not get hist_today!'
                            stroki[4]  = err_msg
                            cntr.log.wr_log_error(err_msg)

                    if ((tm_s % 59) == 0):
                        if cntr.term.str_in_file:
                            rrq = prepair_www_file(cntr)
                            if rrq[0] == 0:
                                rewrite_www_file(rrq[1])
                                stroki[4]  = buf_txt_status + '   rewrite_www_file - OK '
                        else:
                            stroki[4]  = 'str_in_file is EMPTY'

                sg_txt[1].Update(''.join(stroki))

        time.sleep(0.2)

    return 0
#=======================================================================
class Class_LOGGER():
    def __init__(self):
        #self.logger = logging.getLogger(__name__)
        self.logger = logging.getLogger('__main__')
        self.logger.setLevel(logging.INFO)
        # create a file handler
        self.handler = logging.FileHandler('_logger.log')
        self.handler.setLevel(logging.INFO)
        # create a logging format
        #self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        # add the handlers to the logger
        self.logger.addHandler(self.handler)
    #-------------------------------------------------------------------
    def wr_log_info(self, msg):
        self.logger.info(msg)
    #-------------------------------------------------------------------
    def wr_log_error(self, msg):
        self.logger.error(msg)
#=======================================================================
class Class_ACCOUNT():
    def __init__(self):
        self.acc_date = ''
        self.acc_balance = 0.0
        self.acc_profit  = 0.0
        self.acc_go      = 0.0
        self.acc_depo    = 0.0
#=======================================================================
class Class_FUT():
    def __init__(self):
        self.sP_code = "-"
        self.sRest = 0
        self.sVar_margin = 0.0
        self.sOpen_price = 0.0
        self.sLast_price = 0.0
        self.sAsk =  0.0
        self.sBuy_qty = 0
        self.sBid =  0.0
        self.sSell_qty = 0
        self.sFut_go = 0.0
#=======================================================================
class Class_TERM():
    def __init__(self, path_trm):
        self.nm = ''
        self.path_trm = path_trm
        #self.dt_file_size = 0
        self.dt_file = 0        # curv stamptime data file from TERM
        self.dt_data = 0        # curv stamptime DATA/TIME from TERM
        self.str_in_file = []   # list of strings from trm
        self.data_fut = []      # list of Class_FUT() from trm
        self.account  = ''      # obj Class_ACCOUNT() from trm
        self.str_for_hist = ''  # str for hist table
        self.delay_tm = 10      # min period to get data for DB (10 sec)
        #
        self.sec_10_00 = 36000      # seconds from 00:00 to 10:00
        self.sec_14_00 = 50400      # seconds from 00:00 to 14:00
        self.sec_14_05 = 50700      # seconds from 00:00 to 14:05
        self.sec_18_45 = 67500      # seconds from 00:00 to 18:45
        self.sec_19_05 = 68700      # seconds from 00:00 to 19:05
        self.sec_23_45 = 85500      # seconds from 00:00 to 23:45
    #-------------------------------------------------------------------
    def rd_term(self):
        #--- check file cntr.file_path_DATA ----------------------------
        if not os.path.isfile(self.path_trm):
            err_msg = 'can not find file'
            #cntr.log.wr_log_error(err_msg)
            return [1, err_msg]
        buf_stat = os.stat(self.path_trm)
        #
        #--- check size of file ----------------------------------------
        if buf_stat.st_size == 0:
            err_msg = 'size DATA file is NULL'
            #cntr.log.wr_log_error(err_msg)
            return [2, err_msg]
        #
        #--- check time modificated of file ----------------------------
        if int(buf_stat.st_mtime) == self.dt_file:
            str_dt_file = datetime.fromtimestamp(self.dt_file).strftime('%H:%M:%S')
            return [3, 'FILE is not modificated']
        else:
            #self.dt_file_prev = self.dt_file
            self.dt_file = int(buf_stat.st_mtime)
            #print(self.dt_file)
        #
        #--- read TERM file --------------------------------------------
        buf_str = []
        with open(self.path_trm,"r") as fh:
            buf_str = fh.read().splitlines()
        #
        #--- check size of list/file -----------------------------------
        if len(buf_str) == 0:
            err_msg = ' the size buf_str is NULL'
            #cntr.log.wr_log_error(err_msg)
            return [4, err_msg]
        #
        #--- check modificated DATE/TIME of term ! ---------------------
        #--- It's should be more then 10 sec ---------------------------
        try:
            dt_str = buf_str[0].split('|')[0]
            dt_datetime = datetime.strptime(dt_str, '%d.%m.%Y %H:%M:%S')
            dt_sec = dt_datetime.replace(tzinfo=timezone.utc).timestamp()      # real UTC
            if (dt_sec - self.dt_data) > self.delay_tm:
                self.dt_data = dt_sec
            else:
                str_dt_data = datetime.fromtimestamp(self.dt_data).strftime('%H:%M:%S')
                err_msg = 'DATA is not updated ' + dt_str
                #cntr.log.wr_log_error(err_msg)
                return [5, err_msg]
        except Exception as ex:
            err_msg = dt_str + ' => ' + str(ex)
            #cntr.log.wr_log_error(err_msg)
            return [6, err_msg]
        #
        #--- check MARKET time from 10:00 to 23:45 ---------------------
        #term_dt = cntr.term.str_in_file[0].split('|')[0]
        term_dt = buf_str[0].split('|')[0]
        dtt = datetime.strptime(str(term_dt), "%d.%m.%Y %H:%M:%S")
        cur_time = dtt.second + 60 * dtt.minute + 60 * 60 * dtt.hour
        if not (
            (cur_time > self.sec_10_00  and # from 10:00 to 14:00
            cur_time < self.sec_14_00) or
            (cur_time > self.sec_14_05  and # from 14:05 to 18:45
            cur_time < self.sec_18_45) or
            (cur_time > self.sec_19_05  and # from 19:05 to 23:45
            cur_time < self.sec_23_45)):
                err_msg = 'it is not MARKET time now'
                #cntr.log.wr_log_error(err_msg)
                return [7, err_msg]
        #
        #--- compare new DATA with old ---------------------------------
        new_data = buf_str[2:]
        old_data = self.str_in_file[2:]
        buf_len = len(list(set(new_data) - set(old_data)))
        if  buf_len == 0:
            err_msg = 'ASK/BID did not change'
            #cntr.log.wr_log_error(err_msg)
            return [8, err_msg]
        #---  you will do more checks in the future!!!  ----------------
        #--- check ASK != 0  -------------------------------------------
        #--- check BID != 0  -------------------------------------------
        #--- check ASK < BID -------------------------------------------
        #
        self.str_in_file = []
        self.str_in_file = buf_str[:]
        #
        return [0, 'OK']
    #-------------------------------------------------------------------
    def parse_str_in_file(self):
        try:
            self.data_fut = []
            self.account  = Class_ACCOUNT()
            # format of list data_fut:
            #   0   => string of DATA / account.acc_date
            #   1   => [account.acc_balance/acc_profit/acc_go/acc_depo]
            #   2 ... 22  => Class_FUT()
            #print(self.str_in_file)

            for i, item in enumerate(list(self.str_in_file)):
                list_item = ''.join(item).replace(',','.').split('|')
                if   i == 0:
                    self.account.acc_date  = list_item[0]
                    self.data_fut.append(self.account.acc_date)
                elif i == 1:
                    self.account.acc_balance = float(list_item[0])
                    self.account.acc_profit  = float(list_item[1])
                    self.account.acc_go      = float(list_item[2])
                    self.account.acc_depo    = float(list_item[3])
                    self.data_fut.append([self.account.acc_balance,
                                            self.account.acc_profit,
                                            self.account.acc_go,
                                            self.account.acc_depo ])
                else:
                    b_fut = Class_FUT()
                    b_fut.sP_code      = list_item[0]
                    b_fut.sRest        = int  (list_item[1])
                    b_fut.sVar_margin  = float(list_item[2])
                    b_fut.sOpen_price  = float(list_item[3])
                    b_fut.sLast_price  = float(list_item[4])
                    b_fut.sAsk         = float(list_item[5])
                    b_fut.sBuy_qty     = int  (list_item[6])
                    b_fut.sBid         = float(list_item[7])
                    b_fut.sSell_qty    = int  (list_item[8])
                    b_fut.sFut_go      = float(list_item[9])
                    self.data_fut.append(b_fut)
            #print('cntr.data_fut => \n', cntr.data_fut)
        except Exception as ex:
            err_msg = 'parse_str_in_file / ' + str(ex)
            print(err_msg)
            #cntr.log.wr_log_error(err_msg)
            return [1, err_msg]
        return [0, 'ok']
    #-------------------------------------------------------------------
    def prpr_str_hist(self):
        try:
            if self.str_in_file != '':
                for i, item in enumerate(self.str_in_file):
                    list_item = ''.join(item).replace(',','.').split('|')
                    if   i == 0:
                        str_hist = item.split('|')[0] + '|'
                    elif i == 1:
                        pass
                    else:
                        b_str = item.split('|')
                        str_hist += b_str[5] + '|' + b_str[7] + '|'
                self.str_for_hist = str_hist
            else:
                return [0, 'str_in_file is empty!']
        except Exception as ex:
            err_msg = 'prepare_str_hist => ' + str(ex)
            #cntr.log.wr_log_error(err_msg)
            return [1, err_msg]
        return [0, 'OK']
#=======================================================================
class Class_SQLite():
    def __init__(self, path_db):
        self.path_db = path_db
        self.table_db = []
        self.conn = ''
        self.cur = ''
    #-------------------------------------------------------------------
    def check_db(self):
        '''  check FILE of DB SQLite    -----------------------------'''
        #    return os.stat: if FILE is and size != 0
        r_check_db = [0, '']
        name_path_db = self.path_db
        if not os.path.isfile(name_path_db):
            r_check_db = [1, 'can not find file']
        else:
            buf_st = os.stat(name_path_db)
            if buf_st.st_size == 0:
                r_check_db = [1, buf_st]
            else:
                r_check_db = [0, buf_st]
        return r_check_db
    #-------------------------------------------------------------------
    def reset_table_db(self, name_tbl):
        ''' reset data in table DB  ---------------------------------'''
        r_reset_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.execute("DELETE FROM " + name_tbl)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_reset_tbl = [0, 'OK']
        except Exception as ex:
            r_reset_tbl = [1, str(ex)]
        return r_reset_tbl
    #-------------------------------------------------------------------
    def rewrite_table(self, name_tbl, name_list, val = '(?, ?)'):
        ''' rewrite data from table ARCHIV_PACK & PACK_TODAY & DATA ----'''
        r_rewrt_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.execute("DELETE FROM " + name_tbl)
            self.cur.executemany("INSERT INTO " + name_tbl + " VALUES" + val, name_list)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_rewrt_tbl = [0, 'OK']
        except Exception as ex:
            r_rewrt_tbl = [1, str(ex)]
        return r_rewrt_tbl
    #-------------------------------------------------------------------
    def write_table_db(self, name_tbl, name_list):
        ''' write data string into table DB  ------------------------'''
        r_write_tbl = [0, '']
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cur = self.conn.cursor()
            self.cur.executemany("INSERT INTO " + name_tbl + " VALUES(?, ?)", name_list)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            r_write_tbl = [0, 'OK']
        except Exception as ex:
            r_write_tbl = [1, str(ex)]
        return r_write_tbl
    #-------------------------------------------------------------------
    def get_table_db_with(self, name_tbl):
        ''' read one table DB  --------------------------------------'''
        r_get_table_db = []
        self.conn = sqlite3.connect(self.path_db)
        try:
            with self.conn:
                self.cur = self.conn.cursor()
                #self.cur.execute("PRAGMA busy_timeout = 3000")   # 3 s
                self.cur.execute("SELECT * from " + name_tbl)
                self.table_db = self.cur.fetchall()    # read table name_tbl
                r_get_table_db = [0, self.table_db]
        except Exception as ex:
            r_get_table_db = [1, name_tbl + str(ex)]

        return r_get_table_db
#=======================================================================
class Class_PACK():
    def __init__(self):
        self.ind= 0
        self.dt = ''
        self.tm = ''
        self.pAsk = 0.0
        self.pBid = 0.0
        self.EMAf = 0.0
        self.EMAf_rnd = 0.0
        self.cnt_EMAf_rnd = 0.0
        self.AMA = 0.0
        self.AMA_rnd = 0.0
        self.cnt_AMA_rnd = 0.0
#=======================================================================
class Class_Model():
    def __init__(self):
        #self.contr = contr
        #self.hist_Pack = []             # array data of Class_PACK()
        self.archiv_pack = []           # array data of Class_PACK()
        self.archiv_pack_today  = []    # array data of Class_PACK()
        self.name_Pack =''
        self.koef = []
        self.ind = []
        self.kf = []
        self.ema = []
        self.ama = []
        self.null_prc = 0
        self.k_ema, self.k_ema_rnd = 0, 0
        self.fSC, self.sSC, self.nn, self.k_ama_rnd = 0.0, 0.0, 0, 0
        self.alarm_CNT_EMA = False
        self.alarm_CNT_AMA = False
    #-------------------------------------------------------------------
    def calc_koefs_pack(self):
        for item in self.koef:
            self.ind.append(int(item.split(':')[0]))
            self.kf.append(int(item.split(':')[1]))
        self.k_ema = int(self.ema.split(':')[0])
        self.k_ema_rnd = int(self.ema.split(':')[1])
        self.fSC   = float(self.ama.split(':')[0])
        self.sSC   = float(self.ama.split(':')[1])
        self.nn    = int(self.ama.split(':')[2])
        self.k_ama_rnd = int(self.ama.split(':')[3])
#=======================================================================
class Class_CONTR():
    ''' There are 2 history tables of FUT -
    file_path_DATA  - file data from terminal QUIK
    db_path_FUT     - TABLE s_hist_1, ask/bid from TERMINAL 1 today (TF = 15 sec)
    db_path_FUT_arc - TABLE archiv,   ask/bid for period  (TF = 60 sec)
    TABLE total_pack_archiv should update one time per DAY
    TABLE total_pack_today  should update one time per MINUTE
    '''
    def __init__(self, file_path_DATA, db_path_FUT, db_path_FUT_arc):
        #
        self.file_path_DATA  = file_path_DATA    # path file DATA
        self.term            = Class_TERM(self.file_path_DATA)
        #
        self.db_path_FUT  = db_path_FUT       # path DB data & hist
        self.db_FUT_data  = Class_SQLite(self.db_path_FUT)
        #
        self.db_path_FUT_arc = db_path_FUT_arc   # path DB archiv
        self.db_FUT_arc      = Class_SQLite(self.db_path_FUT_arc)
        #
        self.hist_fut = []   # массив котировок фьючей hist 60 s  (today)
        self.arch_fut = []   # массив котировок фьючей ARCHIV 60 s(period)
        #
        self.mdl = []         # list objects MODEL/PACK
        #
        self.log  = Class_LOGGER()
        self.log.wr_log_info('*** START ***')
#=======================================================================
def init_cntr(cntr):
    #--- init FUT cntr.data_fut & cntr.account -------------
    rq  = get_table_data(cntr)
    if rq[0] != 0:
        err_msg = 'init_cntr => ' + rq[1]
        cntr.log.wr_log_error(err_msg)
        sg.Popup('Error !', err_msg)
        return [1, err_msg]

    #--- init koef -----------------------------------------
    cntr.mdl = []
    get_cfg_packts(cntr)

    #--- read DB & init pack_archiv -------------------------
    if not os.path.isfile(cntr.db_path_FUT_arc):
        err_msg = 'can not find file ' + cntr.db_path_FUT_arc
        cntr.log.wr_log_error(err_msg)
        sg.Popup('Error !', err_msg)
        return [1, err_msg]

    #--- init archiv_fut ------------------------------------
    if get_table_ARCHIV_FUT(cntr) == False:
        return [1, 'Error get_table_ARCHIV_FUT']

    # start calc cntr.mdl[i_mdl].null_prc ---------------------
    ktem = (cntr.arch_fut[0][1].replace(',', '.')).split('|')
    #print('\nstart calc NULL price for all packets \n', ktem)
    for i_mdl, item in enumerate(cntr.mdl):
        ask_p, bid_p = 0, 0
        for jdx, jtem in enumerate(cntr.mdl[i_mdl].kf):
            ask_j = float(ktem[1 + 2*cntr.mdl[i_mdl].ind[jdx]])
            bid_j = float(ktem[1 + 2*cntr.mdl[i_mdl].ind[jdx] + 1])
            if jtem > 0 :
                ask_p = ask_p + jtem * ask_j
                bid_p = bid_p + jtem * bid_j
            if jtem < 0 :
                ask_p = ask_p + jtem * bid_j
                bid_p = bid_p + jtem * ask_j
        cntr.mdl[i_mdl].null_prc = int((ask_p + bid_p)/2)
        #print('NULL price for ' + str(i_mdl) + ' = ' + str(cntr.mdl[i_mdl].null_prc))

    #--- init cntr.mdl[i_mdl].archiv_pack --------------------
    rq  = cntr.db_FUT_arc.get_table_db_with('archiv_pack')
    if rq[0] != 0:
        err_msg = 'archiv_pack ' + rq[1]
        cntr.log.wr_log_error()
        sg.Popup('Error !', err_msg)
        return [1, err_msg]
    #--- compare len cntr.mdl[0].archiv_pack vs cntr.arch_fut ---
    if len(cntr.arch_fut) != len(rq[1]):
        err_msg  = 'LEN(arch_fut)     = ' + str(len(cntr.arch_fut))
        err_msg += '\nLEN(archiv_pack)= ' + str(len(rq[1]))
        err_msg += '\nYou must push menu Calc/Calc ARCHIV_PACK'
        cntr.log.wr_log_error(err_msg)
        sg.Popup('Error !', err_msg)
        return [0, err_msg]
    print(40*'>')
    for i_item, item in enumerate(rq[1]):
        if i_item % 1000 == 0:
            print('*', end="", flush=True)
        # item[0] = 1534154466
        # item[1] = 13.08.2018 10:01:06 245 278 2,3 100 1 0 0 0|-57 -22 -0,3 0 0 0 0 0|
        buf_item_1 = item[1].replace(',', '.').split('|')[:-1]
        b_dt = buf_item_1[0].split(' ')[0]
        b_tm = buf_item_1[0].split(' ')[1]
        for i_mdl, jtem in enumerate(buf_item_1):
            buf_pack = Class_PACK()
            buf_pack.ind = item[0]
            buf_pack.dt = b_dt
            buf_pack.tm = b_tm
            buf_jtem = jtem.split(' ')
            i_ind = 2 if (i_mdl == 0) else 0
            buf_pack.pAsk         = float(buf_jtem[0+i_ind])
            buf_pack.pBid         = float(buf_jtem[1+i_ind])
            buf_pack.EMAf         = float(buf_jtem[2+i_ind])
            buf_pack.EMAf_rnd     = float(buf_jtem[3+i_ind])
            buf_pack.cnt_EMAf_rnd = int(buf_jtem[4+i_ind])
            buf_pack.AMA          = float(buf_jtem[5+i_ind])
            buf_pack.AMA_rnd      = float(buf_jtem[6+i_ind])
            buf_pack.cnt_AMA_rnd  = int(buf_jtem[7+i_ind])
            cntr.mdl[i_mdl].archiv_pack.append(buf_pack)

    #--- init pack_today will do in cycle with period 1 minute !!!
    #calc_today_packets(cntr)

    print('\ninit_cntr - OK')
    return [0, 'OK']
#=======================================================================
def get_cfg_packts(cntr):
    rq  = cntr.db_FUT_data.get_table_db_with('cfg_packts')
    if rq[0] != 0:
        sg.Popup('Error cfg_packts!',  rq[1])
        return [1, rq[1]]
    else:
        for i_mdl, item in enumerate(rq[1]):
            cntr.mdl.append(Class_Model())
            ## cntr.db_PACK_data.table_db[i_mdl]) string of koef mdl/pack =>
            ##   ('pckt0', '0:2:SR,9:-20:MX', '222:100', '0.1:0.01:22:100')
            cntr.mdl[i_mdl].name_Pack = rq[1][i_mdl][0]
            cntr.mdl[i_mdl].koef      = rq[1][i_mdl][1].split(',')
            cntr.mdl[i_mdl].ema       = rq[1][i_mdl][2]
            cntr.mdl[i_mdl].ama       = rq[1][i_mdl][3]
            cntr.mdl[i_mdl].calc_koefs_pack()
        return [0, 'OK']
#=======================================================================
def write_hist_DB(cntr):    # write ONLY one string (add into end table)
    nm_table = 'hist_today'
    buf_s = (cntr.term.dt_data, cntr.term.str_for_hist)
    duf_list = []
    duf_list.append(buf_s)
    req = cntr.db_FUT_data.write_table_db(nm_table, duf_list)
    return req
#=======================================================================
def convert_sql_txt(cntr, arr):
    arr_hist = arr
    hist_out = []
    if len(arr_hist) != 0:
        hist_out = []
        hist_out_report = []
        hist_out_archiv = []
        buf_index  = buf_60_sec = 0
        buf_date_time = ''
        #
        last_day = arr_hist[-1][1].split(' ')[0]
        term_dt = arr_hist[-1][1].split('|')[0]
        dtt = datetime.strptime(str(term_dt), "%d.%m.%Y %H:%M:%S")
        #
        for item in arr_hist:
            if last_day in item[1]:
                str_bf = []
                # convert TUPLE in LIST & delete last '|'
                str_bf = ''.join(list(item[1])[0:-1])
                hist_out.append(str_bf)

                if len(hist_out_report) == 0:
                    hist_out_report.append('Start = > ' + item[1].split('|')[0])
                else:
                    if (item[0] - buf_index) > 61:
                        hist_out_report.append('Delay from ' + buf_date_time + ' to ' + item[1].split('|')[0].split(' ')[1])
                buf_index = item[0]
                buf_date_time = item[1].split('|')[0].split(' ')[1]

                if len(hist_out_archiv) == 0:
                    hist_out_archiv.append(item)
                    buf_60_sec = item[0]
                else:
                    if (item[0] - buf_60_sec) > 59:
                        hist_out_archiv.append(item)
                        buf_60_sec = item[0]
        #
        str_month = str(dtt.month)
        if dtt.month < 10:       str_month = '0' + str(dtt.month)
        str_day = str(dtt.day)
        if dtt.day < 10:           str_day = '0' + str(dtt.day)
        #
        path_file = str(dtt.year) + '-' + str_month + '-' + str_day + '_report' + '.txt'
        cntr.log.wr_log_info('Report export for ' + path_file)
        if os.path.exists(path_file):  os.remove(path_file)
        f = open(path_file,'w')
        for item in hist_out_report:   f.writelines(item + '\n')
        f.close()
        #
        path_file = str(dtt.year) + '-' + str_month + '-' + str_day + '_archiv_fut' + '.csv'
        cntr.log.wr_log_info('Archiv for ' + path_file)
        if os.path.exists(path_file):  os.remove(path_file)
        f = open(path_file,'w')
        for item in hist_out_archiv:   f.writelines(str(int(item[0])) + ';' + item[1] + '\n')
        f.close()
        #
        path_file = str(dtt.year) + '-' + str_month + '-' + str_day + '_hist_ALFA' + '.txt'
        if os.path.exists(path_file):  os.remove(path_file)
        f = open(path_file,'w')
        for item in hist_out:          f.writelines(item + '\n')
        f.close()
        cntr.log.wr_log_info('Hist export for ' + path_file)
#=======================================================================
def calc_archiv_packets(cntr):
    #   calc_archiv_packets for every models ---------------
    for i_mdl, item_mdl in enumerate(cntr.mdl):
        sg.OneLineProgressMeter('calc_archiv_packets', i_mdl+1, 11, 'key')
        cntr.mdl[i_mdl].archiv_pack = []       # array data of Class_PACK()
        calc_archiv_packets_mdl(cntr, i_mdl)
#=======================================================================
def calc_archiv_packets_mdl(cntr, i_mdl):
    arr_HIST = cntr.arch_fut  # archiv of FUT 60 sec
    const_UP, const_DW = +50, -50
    koef = round(2/(1+cntr.mdl[i_mdl].k_ema),5)
    for idx, item_HIST in enumerate(arr_HIST):
        ask_p, bid_p = 0, 0
        buf_c_pack = Class_PACK()
        buf_c_pack.ind = item_HIST[0]
        item = (item_HIST[1].replace(',', '.')).split('|')
        #print(item)
        buf_c_pack.dt, buf_c_pack.tm  = item[0].split(' ')
        for jdx, jtem in enumerate(cntr.mdl[i_mdl].kf):
            ask_j = float(item[1 + 2*cntr.mdl[i_mdl].ind[jdx]])
            bid_j = float(item[1 + 2*cntr.mdl[i_mdl].ind[jdx] + 1])
            if jtem > 0 :
                ask_p = ask_p + jtem * ask_j
                bid_p = bid_p + jtem * bid_j
            if jtem < 0 :
                ask_p = ask_p + jtem * bid_j
                bid_p = bid_p + jtem * ask_j

        ask_bid_AVR = 0
        if idx == 0:
            #cntr.mdl[i_mdl].null_prc = int((ask_p + bid_p)/2)
            buf_c_pack.pAsk, buf_c_pack.pBid = 0, 0
            buf_c_pack.EMAf, buf_c_pack.EMAf_rnd = 0, 0
            buf_c_pack.AMA, buf_c_pack.AMA_rnd = 0, 0
            buf_c_pack.cnt_EMAf_rnd = 0
            buf_c_pack.cnt_AMA_rnd = 0

        else:
            ask_p = int(ask_p - cntr.mdl[i_mdl].null_prc)
            bid_p = int(bid_p - cntr.mdl[i_mdl].null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.mdl[i_mdl].archiv_pack[idx-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef, 1)
            buf_c_pack.EMAf_rnd = cntr.mdl[i_mdl].k_ema_rnd * math.ceil(buf_c_pack.EMAf / cntr.mdl[i_mdl].k_ema_rnd )

            prev_EMAf_rnd = cntr.mdl[i_mdl].archiv_pack[idx-1].EMAf_rnd
            i_cnt = cntr.mdl[i_mdl].archiv_pack[idx-1].cnt_EMAf_rnd
            if prev_EMAf_rnd > buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_EMAf_rnd < buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_EMAf_rnd = i_cnt

            if idx > cntr.mdl[i_mdl].nn:
                sgnal_AMA = abs(cntr.mdl[i_mdl].archiv_pack[idx-1].pAsk - cntr.mdl[i_mdl].archiv_pack[idx-cntr.mdl[i_mdl].nn-1].pAsk)
                noise_AMA = 0
                for ii in range(2, cntr.mdl[i_mdl].nn - 2):
                    noise_AMA += abs(cntr.mdl[i_mdl].archiv_pack[idx-ii].pAsk - cntr.mdl[i_mdl].archiv_pack[idx-ii-1].pAsk)
                if noise_AMA == 0:
                    er_AMA = 0
                else:
                    er_AMA = round( (sgnal_AMA / noise_AMA) ,3)
                #buf_p.koef_er_AMA = er_AMA
                ssc_AMA = (er_AMA * (cntr.mdl[i_mdl].fSC-cntr.mdl[i_mdl].sSC)) + cntr.mdl[i_mdl].sSC
                prev = cntr.mdl[i_mdl].archiv_pack[idx-1].AMA
                buf_c_pack.AMA = prev + int(round(ssc_AMA * ssc_AMA * (ask_bid_AVR - prev)))
            else:
                buf_c_pack.AMA = cntr.mdl[i_mdl].archiv_pack[idx-1].AMA
            buf_c_pack.AMA_rnd = cntr.mdl[i_mdl].k_ama_rnd * math.ceil(buf_c_pack.AMA / cntr.mdl[i_mdl].k_ama_rnd)

            prev_AMA_rnd = cntr.mdl[i_mdl].archiv_pack[idx-1].AMA_rnd
            i_cnt = cntr.mdl[i_mdl].archiv_pack[idx-1].cnt_AMA_rnd
            if prev_AMA_rnd > buf_c_pack.AMA_rnd:
                buf_c_pack.cnt_AMA_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_AMA_rnd < buf_c_pack.AMA_rnd:
                buf_c_pack.cnt_AMA_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_AMA_rnd = i_cnt

        cntr.mdl[i_mdl].archiv_pack.append(buf_c_pack)
#=======================================================================
def prepair_archiv_pack(cntr):
    name_list =[]
    for i_hist, item_hist in enumerate(cntr.mdl[0].archiv_pack):
        buf_dt = item_hist.dt + ' ' + item_hist.tm + ' '
        buf_s = ''
        for i_mdl, item_mdl in enumerate(cntr.mdl):
            buf = cntr.mdl[i_mdl].archiv_pack[i_hist]
            buf_s += str(buf.pAsk) + ' ' + str(buf.pBid)     + ' '
            buf_s += str(buf.EMAf) + ' ' + str(buf.EMAf_rnd) + ' ' + str(buf.cnt_EMAf_rnd) + ' '
            buf_s += str(buf.AMA)  + ' ' + str(buf.AMA_rnd)  + ' ' + str(buf.cnt_AMA_rnd) + '|'
        name_list.append((item_hist.ind, buf_dt + buf_s.replace('.', ',')))
    return name_list
#=======================================================================
def calc_today_packets(cntr):
    #   calc_today_packets for every models ---------------
    for i_mdl, item_mdl in enumerate(cntr.mdl):
        #sg.OneLineProgressMeter('calc_today_packets', i_mdl+1, 11, 'key')
        cntr.mdl[i_mdl].archiv_pack_today = []       # array data of Class_PACK()
        calc_today_packets_mdl(cntr, i_mdl)
#=======================================================================
def calc_today_packets_mdl(cntr, i_mdl):
    arr_HIST = cntr.hist_fut  # hist of FUT 60 sec (TODAY)
    const_UP, const_DW = +50, -50
    koef = round(2/(1+cntr.mdl[i_mdl].k_ema),5)
    for idx, item_HIST in enumerate(arr_HIST):
        ask_p, bid_p = 0, 0
        buf_c_pack = Class_PACK()
        buf_c_pack.ind = item_HIST[0]
        item = (item_HIST[1].replace(',', '.')).split('|')
        buf_c_pack.dt, buf_c_pack.tm  = item[0].split(' ')
        for jdx, jtem in enumerate(cntr.mdl[i_mdl].kf):
            ask_j = float(item[1 + 2*cntr.mdl[i_mdl].ind[jdx]])
            bid_j = float(item[1 + 2*cntr.mdl[i_mdl].ind[jdx] + 1])
            if jtem > 0 :
                ask_p = ask_p + jtem * ask_j
                bid_p = bid_p + jtem * bid_j
            if jtem < 0 :
                ask_p = ask_p + jtem * bid_j
                bid_p = bid_p + jtem * ask_j

        ask_bid_AVR = 0
        if idx == 0:
            ask_p = int(ask_p - cntr.mdl[i_mdl].null_prc)
            bid_p = int(bid_p - cntr.mdl[i_mdl].null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.mdl[i_mdl].archiv_pack[-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef, 1)
            buf_c_pack.EMAf_rnd = cntr.mdl[i_mdl].k_ema_rnd * math.ceil(buf_c_pack.EMAf / cntr.mdl[i_mdl].k_ema_rnd )
            buf_c_pack.cnt_EMAf_rnd =  cntr.mdl[i_mdl].archiv_pack[-1].cnt_EMAf_rnd

            buf_c_pack.AMA, buf_c_pack.AMA_rnd = cntr.mdl[i_mdl].archiv_pack[-1].AMA, cntr.mdl[i_mdl].archiv_pack[-1].AMA_rnd
            buf_c_pack.cnt_AMA_rnd =  cntr.mdl[i_mdl].archiv_pack[-1].cnt_AMA_rnd

        else:
            ask_p = int(ask_p - cntr.mdl[i_mdl].null_prc)
            bid_p = int(bid_p - cntr.mdl[i_mdl].null_prc)
            buf_c_pack.pAsk = ask_p
            buf_c_pack.pBid = bid_p
            ask_bid_AVR = int((ask_p + bid_p)/2)

            prev_EMAf = cntr.mdl[i_mdl].archiv_pack_today[idx-1].EMAf
            buf_c_pack.EMAf = round(prev_EMAf + (ask_bid_AVR - prev_EMAf) * koef, 1)
            buf_c_pack.EMAf_rnd = cntr.mdl[i_mdl].k_ema_rnd * math.ceil(buf_c_pack.EMAf / cntr.mdl[i_mdl].k_ema_rnd )

            prev_EMAf_rnd = cntr.mdl[i_mdl].archiv_pack_today[idx-1].EMAf_rnd
            i_cnt = cntr.mdl[i_mdl].archiv_pack_today[idx-1].cnt_EMAf_rnd
            if prev_EMAf_rnd > buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_EMAf_rnd < buf_c_pack.EMAf_rnd:
                buf_c_pack.cnt_EMAf_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_EMAf_rnd = i_cnt

            if idx > cntr.mdl[i_mdl].nn:
                sgnal_AMA = abs(cntr.mdl[i_mdl].archiv_pack_today[idx-1].pAsk - cntr.mdl[i_mdl].archiv_pack_today[idx-cntr.mdl[i_mdl].nn-1].pAsk)
                noise_AMA = 0
                for ii in range(2, cntr.mdl[i_mdl].nn - 2):
                    noise_AMA += abs(cntr.mdl[i_mdl].archiv_pack_today[idx-ii].pAsk - cntr.mdl[i_mdl].archiv_pack_today[idx-ii-1].pAsk)
                if noise_AMA == 0:
                    er_AMA = 0
                else:
                    er_AMA = round( (sgnal_AMA / noise_AMA) ,3)
                #buf_p.koef_er_AMA = er_AMA
                ssc_AMA = (er_AMA * (cntr.mdl[i_mdl].fSC-cntr.mdl[i_mdl].sSC)) + cntr.mdl[i_mdl].sSC
                prev = cntr.mdl[i_mdl].archiv_pack_today[idx-1].AMA
                buf_c_pack.AMA = prev + int(round(ssc_AMA * ssc_AMA * (ask_bid_AVR - prev)))
            else:
                buf_c_pack.AMA = cntr.mdl[i_mdl].archiv_pack_today[idx-1].AMA
            buf_c_pack.AMA_rnd = cntr.mdl[i_mdl].k_ama_rnd * math.ceil(buf_c_pack.AMA / cntr.mdl[i_mdl].k_ama_rnd)

            prev_AMA_rnd = cntr.mdl[i_mdl].archiv_pack_today[idx-1].AMA_rnd
            i_cnt = cntr.mdl[i_mdl].archiv_pack_today[idx-1].cnt_AMA_rnd
            if prev_AMA_rnd > buf_c_pack.AMA_rnd:
                buf_c_pack.cnt_AMA_rnd = 0 if i_cnt > 0 else i_cnt-1
            elif prev_AMA_rnd < buf_c_pack.AMA_rnd:
                buf_c_pack.cnt_AMA_rnd = 0 if i_cnt < 0 else i_cnt+1
            else:
                buf_c_pack.cnt_AMA_rnd = i_cnt

        cntr.mdl[i_mdl].archiv_pack_today.append(buf_c_pack)
#=======================================================================
def prepair_today_pack(cntr):
    name_list =[]
    for i_hist, item_hist in enumerate(cntr.mdl[0].archiv_pack_today):
        buf_dt = item_hist.dt + ' ' + item_hist.tm + ' '
        buf_s = ''
        for i_mdl, item_mdl in enumerate(cntr.mdl):
            buf = cntr.mdl[i_mdl].archiv_pack_today[i_hist]
            buf_s += str(buf.pAsk) + ' ' + str(buf.pBid)     + ' '
            buf_s += str(buf.EMAf) + ' ' + str(buf.EMAf_rnd) + ' ' + str(buf.cnt_EMAf_rnd) + ' '
            buf_s += str(buf.AMA)  + ' ' + str(buf.AMA_rnd)  + ' ' + str(buf.cnt_AMA_rnd) + '|'
        name_list.append((item_hist.ind, buf_dt + buf_s.replace('.', ',')))
    return name_list
#=======================================================================
def get_table_ARCHIV_FUT(cntr):
    cntr.arch_fut = []
    rq  = cntr.db_FUT_arc.get_table_db_with('archiv_fut')
    if rq[0] != 0:
        err_msg = 'Calc archiv_fut ' + rq[1]
        cntr.log.wr_log_error(err_msg)
        sg.Popup('Error archiv_fut!', err_msg)
        return False
    else:
        cntr.arch_fut = rq[1][:]
        return True
#=======================================================================
def get_table_data(cntr):
    #--- read table DATA -----------------------------------
    #--- init cntr.data_fut & cntr.account -----------------
    #--- rewrite www file  ---------------------------------
    rq  = cntr.db_FUT_data.get_table_db_with('data')
    if rq[0] == 0:
        cntr.term.str_in_file = rq[1]
        #print('db_FUT_data.get_table_db_with(data) \n', rq[1])
        rq  = cntr.term.parse_str_in_file()
        if rq[0] == 0:
            #print('parse_str_in_file \n', rq[1])
            rq = prepair_www_file(cntr)
            if rq[0] == 0:
                #print('prepair_www_file \n', rq[1])
                rewrite_www_file(rq[1])
            else:
                err_msg = 'get_table_data...rewrite_www_file => ' + rq[1]
                return [1, err_msg]
        else:
            err_msg = 'get_table_data...parse_str_data_fut => ' + rq[1]
            return [1, err_msg]
    else:
        err_msg = 'get_table_db_with(data) ' + rq[1]
        return [1, err_msg]
    return [0, 'ok']
#=======================================================================
def convert_www_file(cdf):
    b_str = ''
    b_str += '|' + str(cdf.sRest) + '.0'
    b_str += '|' + str(cdf.sVar_margin)
    b_str += '|' + str(int((cdf.sAsk+cdf.sBid)/2)) +  '\n'
    return b_str
#=======================================================================
def prepair_www_file(cntr):
    try:
        arr = ['Time','Money','Profit','GO_fut',12 * '*',
                'SBER','GAZP','LKOH','ROSN','BVTB','FGGK','GMKN','SBRP','RTSI','MXI_','curTime']
        for i_row in range(len(arr)):       # number of rows / строки
            if i_row == 0:  #'Date'
                arr[i_row] +=  '|' + cntr.term.account.acc_date.split(' ')[1]
                arr[i_row] +=  '|Date|' + cntr.term.account.acc_date.split(' ')[0] + '\n'
            elif i_row == 1:  #'Money'
                arr[i_row] +=  '|-----|-----|' + str(cntr.term.account.acc_balance) + '\n'
            elif i_row == 2:  #'Profit'
                arr[i_row] +=  '|-----|-----|' + str(cntr.term.account.acc_profit)  + '\n'
            elif i_row == 3:  #'GO_fut'
                arr[i_row] +=  '|-----|-----|' + str(cntr.term.account.acc_go)      + '\n'
            elif i_row == 4:  #12 * '*'
                arr[i_row] +=  '|sRest|margin|ASK_BID' + '\n'
            elif 4 < i_row < (len(arr)-1):  # futures
                #arr[i_row] +=  convert_www_file(cntr.data_fut[i_row-3])
                arr[i_row] +=  convert_www_file(cntr.term.data_fut[i_row-3])
            else:             # 'curTime'
                dt_txt = time.strftime('%d.%m.%Y', time.localtime())
                tm_txt = time.strftime('%H:%M:%S', time.localtime())
                arr[i_row] += '|' + tm_txt + '||' + dt_txt + '\n'

        b_str = ''.join(arr)
        #print(b_str)
    except Exception as ex:
        print(ex)
        err_msg = 'prepair_www_file / ' + str(ex)
        cntr.log.wr_log_error(err_msg)
        return [1, err_msg]
    return [0, b_str]
#=======================================================================
def rewrite_www_file(b_str):
    try:
        pass
        #with open(file_path_WWW, "w") as fh:
        #    fh.write(b_str)
    except Exception as ex:
        err_msg = 'rewrite_WWW_file / ' + ex
        cntr.log.wr_log_error(err_msg)
        return [1, err_msg]
    return [0, 'ok']
#=======================================================================
def menu_buttons(cntr, button):
    '''   analize of MENU button  -----------------------------------'''
    #
    if button == 'SQL tbl DATA':
        cntr.log.wr_log_info('SQL fut DATA')
        rq  = get_table_data(cntr)
        if rq[0] != 0:
            cntr.log.wr_log_error(rq[1])
            sg.Popup('Error !', rq[1])
        else:
            sg.Popup('OK !', cntr.term.str_in_file)
    #
    if button == 'SQL tbls TODAY & ARCHIV':
        cntr.log.wr_log_info('SQL tbls TODAY & ARCHIV')
        #
        rq  = cntr.db_FUT_arc.get_table_db_with('archiv_fut')
        if rq[0] != 0:
            cntr.log.wr_log_error(rq[1])
            sg.Popup('Error !', rq[1])
        else:
            msg = rq[1]
            if len(msg) != 0:
                buf_msg  = 'archiv_fut => ' + '\n'
                buf_msg += 'first => ' + msg[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + msg[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(msg)) + '\n'
                buf_msg += '---------------------------------\n'
            else:
                buf_msg  = 'archiv_fut => NULL' + '\n'
                buf_msg += '---------------------------------\n'
            #sg.Popup('OK !',  buf_msg)
        rq1  = cntr.db_FUT_arc.get_table_db_with('archiv_pack')
        if rq1[0] != 0:
            cntr.log.wr_log_error(rq1[1])
            sg.Popup('Error !', rq1[1])
        else:
            msg = rq1[1]
            if len(msg) != 0:
                buf_msg += 'archiv_pack => ' + '\n'
                buf_msg += 'first => ' + msg[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + msg[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(msg)) + '\n'
                buf_msg += '---------------------------------\n'
            else:
                buf_msg += 'archiv_pack => NULL' + '\n'
                buf_msg += '---------------------------------\n'
            #sg.Popup('OK !',  buf_msg)
        rq  = cntr.db_FUT_data.get_table_db_with('hist_today')
        if rq[0] != 0:
            cntr.log.wr_log_error(rq[1])
            sg.Popup('Error !', rq[1])
        else:
            msg = rq[1]
            if len(msg) != 0:
                buf_msg += 'hist_today => ' + '\n'
                buf_msg += 'first => ' + msg[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + msg[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(msg)) + '\n'
                buf_msg += '---------------------------------\n'
            else:
                buf_msg += 'hist_today => NULL' + '\n'
                buf_msg += '---------------------------------\n'
            #sg.Popup('OK !',  buf_msg)
        rq1  = cntr.db_FUT_data.get_table_db_with('pack_today')
        if rq1[0] != 0:
            cntr.log.wr_log_error(rq1[1])
            sg.Popup('Error !', rq1[1])
        else:
            msg = rq1[1]
            if len(msg) != 0:
                buf_msg += 'pack_today => ' + '\n'
                buf_msg += 'first => ' + msg[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + msg[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(msg)) + '\n' + '\n'
            else:
                buf_msg += 'pack_today => NULL' + '\n'
            sg.Popup('OK !',  buf_msg)
    #
    if button == 'table HIST empty':
        cntr.log.wr_log_info('reset SQL HIST')
        rq  = cntr.db_FUT_data.reset_table_db('hist_today')
        if rq[0] == 0:
            sg.Popup('OK !', 'reset hist_today')
        else:
            msg = 'reset hist_today ' + rq[1]
            cntr.log.wr_log_error(msg)
            sg.Popup('Error !', msg)
        rq  = cntr.db_FUT_data.reset_table_db('pack_today')
        if rq[0] == 0:
            sg.Popup('OK !', 'reset pack_today')
        else:
            msg = 'reset pack_today ' + rq[1]
            cntr.log.wr_log_error(msg)
            sg.Popup('Error !', msg)
    #
    if button == 'convert sql txt':
        cntr.log.wr_log_info('convert sql txt')
        rq  = cntr.db_FUT_data.get_table_db_with('hist_today')
        if rq[0] == 0:
            convert_sql_txt(cntr, rq[1])
            sg.Popup('OK !', 'Check info in log file !')
        else:
            cntr.log.wr_log_error(rq[1])
            sg.Popup('ERROR !', rq[1])
    #
    if button == 'merge hist to archiv':
        cntr.log.wr_log_info('merge HIST into ARCHIV')
        # !!!
        # !!! check last element of HIST  vs first element of S_ARCHIV
        # !!!
        rq  = cntr.db_FUT_data.get_table_db_with('hist_today')
        if rq[0] == 0:
            buf_60_sec = 0
            hist_out_archiv = []
            for item in rq[1]:
                if len(hist_out_archiv) == 0:
                    hist_out_archiv.append(item)
                    buf_60_sec = item[0]
                else:
                    if (item[0] - buf_60_sec) > 59:
                        hist_out_archiv.append(item)
                        buf_60_sec = item[0]
            req = cntr.db_FUT_arc.write_table_db('s_archiv', hist_out_archiv)
            cntr.log.wr_log_info('merge hist to archiv OK')
            sg.Popup('merge hist to archiv', 'Copy complete OK !')
        else:
            cntr.log.wr_log_error(rq[1])
            sg.Popup('ERROR !', rq[1])
    #
    if button == 'Calc pack_today':
        cntr.log.wr_log_info('Calc pack_today')
        rq  = cntr.db_FUT_data.get_table_db_with('hist_today')
        msg = rq[1]
        if rq[0] == 0:
            if len(msg) != 0:
                buf_msg  = 'first => ' + msg[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + msg[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(msg))
                sg.Popup('OK !',  buf_msg)
                # convert from 15 sec to 60 sec
                cntr.hist_fut = []
                last_ind_sec = 0
                for item in msg: # arr_hist_15_s:
                    if (item[0] - last_ind_sec) > 59:
                        last_ind_sec = item[0]
                        cntr.hist_fut.append(item)
                buf_msg  = 'first => ' + cntr.hist_fut[0][1].split('|')[0]  + '\n'
                buf_msg += 'last  => ' + cntr.hist_fut[-1][1].split('|')[0] + '\n'
                buf_msg += 'len   => ' + str(len(cntr.hist_fut))
                sg.Popup('OK !',  buf_msg)
                # calc from cntr.hist_fut  to  cntr.mdl[i_mdl].archiv_pack_today
                calc_today_packets(cntr)
                name_list = []
                name_list = prepair_today_pack(cntr)
                # rewrite to SQL table  pack_today / cntr.db_FUT_data.rewrite_table('pack_today', name_list))
                rq  = cntr.db_FUT_data.rewrite_table('pack_today', name_list)
                if rq[0] != 0:
                    err_msg = 'rewrite_table_arc pack_today' + rq[1]
                    cntr.log.wr_log_error(err_msg)
                    sg.Popup('Error !', err_msg)
                else:
                    cntr.log.wr_log_info('rewrite_table_arc pack_today - OK')
                    sg.Popup('OK !', 'ok rewrite_table_arc  pack_today ' + str(len(name_list)))
            else:
                buf_msg = 'len(hist)   => NULL'
                rq  = cntr.db_FUT_data.reset_table_db('pack_today')
                sg.Popup('NULL !',  buf_msg)

        else:
            cntr.log.wr_log_error('test SQL fut(hist) ' + msg)
            sg.Popup('Error !', msg)
    #
    if button == 'File WWW':
        rq  = cntr.db_FUT_data.get_table_db_with('data')
        if rq[0] == 0:
            cntr.term.str_in_file = rq[1]
            rq = cntr.term.parse_str_in_file()
            if rq[0] == 0:
                rrq = prepair_www_file(cntr)
                if rrq[0] == 0:
                    rewrite_www_file(rrq[1])
                    sg.Popup('OK !','File for WWW is ready !')
        else:
            cntr.log.wr_log_error('test SQL fut(data) ' + msg)
            sg.Popup('Error !', msg)
    #
    if button == 'Calc archiv_pack':
        if get_table_ARCHIV_FUT(cntr) == True:
            calc_archiv_packets(cntr)
            name_list = []
            name_list = prepair_archiv_pack(cntr)
            rq  = cntr.db_FUT_arc.rewrite_table('archiv_pack', name_list)
            if rq[0] != 0:
                err_msg = 'rewrite_table_arc ' + rq[1]
                cntr.log.wr_log_error(err_msg)
                sg.Popup('Error !', err_msg)
            else:
                cntr.log.wr_log_info('rewrite_table_arc - OK')
                sg.Popup('OK !', 'ok rewrite_table_arc ' + str(len(name_list)))
    #
#=======================================================================
if __name__ == '__main__':
    import sys
    sys.exit(main())

