# -*- coding: utf-8 -*-
import urllib.request
from html.parser import HTMLParser
import re
import sqlite3

class PlayNum(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.recording = 0
        self.recwin = 0
        self.recscope = 0
        self.data = []
        self.header = []
        self.winner = []
        self.scope = []

    def handle_starttag(self, tag, attrs):
        if tag != 'div':
            return
        for name, value in attrs:
            if name == 'class' and value == 'cleared game_567 game_5x36':
                self.recording += 1
                break
            elif name == 'class' and value == 'winning_numbers cleared':
                self.recording += 1
                break
            elif name == 'class' and value == 'results_table with_bottom_shadow':
                self.recwin += 1
            elif name == 'class' and value == 'col drawing_details':
                self.recscope += 1
        else:
            return

    def handle_endtag(self, tag):
        if tag == 'div' and self.recording:
            self.recording -= 1
        if tag == 'div' and self.recwin:
            self.recwin -= 1
        if tag == 'div' and self.recscope:
            self.recscope -= 1

    def handle_data(self, data):
        if self.recording == 1:
            self.header.append(data)
        if self.recording == 2:
            for coin2 in data:
                if coin2.isdigit():
                    self.data.append(data)
                    break
        if self.recwin:
            self.winner.append(data)
        if self.recscope:
            self.scope.append(data)

def insertdb(data):
    conn = sqlite3.connect("loto.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO ROUNDS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (data['round'], data['g1'],data['g2'],data['g3'],data['g4'],data['g5'],data['g6'],data['date'],
                        data['tickets'],data['combo'],data['tl_sum'],data['s_pz'],data['pz'],data['guess_num'],
                        data['tl_win'],data['pz_win'],data['tl_pz'])
                    )
        conn.commit()
        print ("Inserted")
    except Exception as ff:
        print (ff)

def createdb():
    conn = sqlite3.connect("loto.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""CREATE TABLE ROUNDS
                        (round integer, g1 integer, g2 integer, g3 integer, g4 integer,g5 integer,g6 integer, date text, 
                        tickets text, combo text, tl_sum text, s_pz text, pz text, guess_num text, tl_win text, pz_win text,
                        tl_pz text)
                        """)
        print ("Cteate DB ROUNDS")
    except Exception as ff:
         print (ff)

def selectall(): # for test
    conn = sqlite3.connect("loto.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM ROUNDS")
        f = cursor.fetchall()
    except Exception as ff:
        print(ff)
    return f

def search_id(r_id):
    conn = sqlite3.connect("loto.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT round FROM ROUNDS WHERE round=?", [r_id])
        f = cursor.fetchall()
    except Exception as ff:
        print (ff)
    return f

try:
    createdb()
except Exception as ff:
    print (ff)

for s in range(9000, 14000):
    url = 'https://www.stoloto.ru/5x36plus/archive/%s' %s
    #check HTTP
    try:
        ch = urllib.request.urlopen(url).getcode()
    except urllib.error.HTTPError:
        ch = 400

    if ch == 200:
        page = urllib.request.urlopen(url)
        html = page.read()
        pars = PlayNum()
        pars.feed(str(html.decode()))
    else:
        print("Not found page")

    # if ch == 200:
    #     pass
    # else:
    #     print ('http error:', ch)

    # Do list after pars
    # data (data, list )
    try:
        # do list with number win number
        data = pars.data
    except:
        print('not match data')

    # Match number game (serial, str)
    try:
        header = pars.header
        serial = re.search (r'\d{4}', str(header))
        serial = serial.group(0)
    except:
        print('not match Number play')

    #Match date for game (date,str)
    date = pars.header
    date = date[1].split(',')
    date = date[1]
    month = {'01':'января','02':'февраля',
             '03':'марта','04':'апреля',
             '05':'мая','06':'июня',
             '07':'июля','08':'августа',
             '09':'сентября','10':'октября',
             '11':'ноября','12':'декабря'
            }
    date = date.split(' ')
    chi = [key for key, value in month.items() if date[2] == value]
    finaldate = "'%s'-'%s'-'%s'-'%s'" % (date[1],chi[0],date[3],date[5])
    date = finaldate
    # Match table (winer, list)
    winers = pars.winner
    winer = []
    for w in winers:
        w = w.strip()
        if w:
            w = w.replace('\xa0','')
            winer.append(w)
    # Match Scope (scope, list)
    scopes = pars.scope
    scope =[]
    for e in scopes:
        e = e.strip()
        if e:
            e = e.replace('\xa0','')
            scope.append(e.strip())

    # Build dict for DBA
    hash_loto = {
        "round": serial, # int
        "g1": data[0], # int
        "g2": data[1], # int
        "g3": data[2], # int
        "g4": data[3],
        "g5": data[4],
        "g6": data[5],
        "date": date.replace("'",''),   # Дата розыгрыша
        "tickets":   scope[1],       # Число билетов, принявших участие в розыгрыше
        "combo":   scope[3],             # Комбинаций
        "tl_sum":   scope[5],      # Сумма, выплаченная по итогам розыгрыша, составила, руб.
        "s_pz":   scope[7],          # Суперприз, руб.
        "pz":   scope[9],             # Приз, руб.
        "guess_num":   winer[4] + "/" + winer[8] + "/" + winer[12] + "/" + winer[16] + "/" + winer[20],     # Угаданных чисел
        "tl_win":   winer[5] + "/" + winer[9] + "/" + winer[13] + "/" + winer[17] + "/" + winer[21],        # Кол-во победителей
        "pz_win":   winer[6] + "/" + winer[10] + "/" + winer[14] + "/" + winer[18] + "/" + winer[22],       # Выигрыш победителя, руб.
        "tl_pz":   winer[7] + "/" + winer[11] + "/" + winer[15] + "/" + winer[19] + "/" + winer[23],    # Общий выигрыш, руб.
    }


    if serial:
        ee = search_id(serial)
        if ee:
            print("Duplicate serial in DB :", serial)
        else:
            insertdb(hash_loto)
            print("Insert in DB :", serial)
