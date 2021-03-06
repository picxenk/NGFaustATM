#!/usr/bin/env python
#coding=utf-8

import sys
import json
import time
import urllib2
import Image, ImageDraw
from bs4 import BeautifulSoup
from twisted.internet import reactor
# from twisted.application import service


## -----------------------------------------------------------------------
## Configuration
## -----------------------------------------------------------------------
faust_atm_home_path = '/home/pi/NGFaustATM/'
sys.path.append(faust_atm_home_path)
from printer import *
from Pubnub import Pubnub

port = ThermalPrinter.SERIALPORT
printer = ThermalPrinter(serialport=port)

publish_key = 'pub-c-36769b01-35f9-4b49-807d-401a21cff9b8'
subscribe_key = 'sub-c-252a6482-e243-11e3-9849-02ee2ddab7fe'
secret_key = 'sec-c-YTBhZmExNzktMGRhNS00NWQyLWFiNTMtMWJiM2VkMDQ0MTk1'
ssl_on = False
channel_name = 'atm2'

info_image = Image.open(faust_atm_home_path+"image2.png")
info_data = list(info_image.getdata())
info_image_w, info_image_h = info_image.size


## -----------------------------------------------------------------------
## Commands
## -----------------------------------------------------------------------
def print_header_on(p):
    #     header = """
    # ╔══════════════════════════════════╗
    # ║                                  ║
    # ║                                  ║
    # ╚══════════════════════════════════╝
    # """
    # header  = chr(0xC9) + chr(0xCD)*30 + chr(0xBB)
    # header += chr(0xBA) + chr(0x20)*30 + chr(0xBA)
    # header += chr(0xC8) + chr(0xCD)*30 + chr(0xBC)
    p.justify("C")
    p.bold_on()
    p.print_text("RECEIPT\n")
    p.bold_off()
    p.font_b_on()
    p.print_text(time.ctime())
    p.font_b_off()
    p.linefeed()


def print_line_on(p):
    # line = "────────────────────────────────────"
    line = chr(0xC4)*32
    p.print_text(line)


def print_info_on(p):
    # i = Image.open("image2.png")
    # data = list(i.getdata())
    # w, h = i.size
    time.sleep(0.5)
    p.print_bitmap(info_data, info_image_w, info_image_h, False)


def print_footer_on(p):
    p.linefeed()
    p.linefeed()
    p.linefeed()


def print_receipt_on(p, message):

    markup_text_1 = """nc Thank you. {userName}!
nc Deal with Mephisto.
nc To get cash by friends.
""".format(**message)
    markup_text_2 = """nr Total Credit: ${totalCredit}
nr Withdrawn Friend Amount: {withdrawListSize}
nr Total Cash: ${cash}
nr Balance: ${credit}
""".format(**message)

    print_header_on(p)
    p.linefeed()

    p.print_markup(markup_text_1)
    p.linefeed()

    print_line_on(p)

    i = 1
    text = ''
    time.sleep(0.5)
    for f in message['withdrawList']:
        if (f['friendName'].isalpha()==False):
            f['friendName'] = make_english_name(f['friendName'])
        text += "%03d" % i
        text += chr(0x0B)
        text += f['friendName']
        text += chr(0x0B)*(20-len(f['friendName']))
        text += f['valueName']
        text += chr(0x0B)*(9-len(f['valueName']))
        text += "$%d\n" % f['valuePrice']
        i += 1

    p.font_b_on()
    p.print_text(text)
    p.font_b_off()

    print_line_on(p)
    p.linefeed()

    p.print_markup(markup_text_2)
    p.linefeed()

    print_info_on(p)
    print_footer_on(p)

def make_english_name(non_english_name):
    url = "http://s.lab.naver.com/translation/?query="+non_english_name+"&where=name"
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html)
    trs = soup.find_all('td', attrs={'class':'cell_engname'})
    if len(trs)>=1:
        return trs[0].text
    else:
        return non_english_name

def message_received(message):
    message['withdrawListSize'] = len(message['withdrawList'])
    message['totalCredit'] = message['credit'] + message['cash']
    if (message['userName'].isalpha()==False):
        message['userName'] = make_english_name(message['userName'])

    print(message)
    print_receipt_on(printer, message)
   

def connected():
    print('Connected')

## -----------------------------------------------------------------------
## Main
## -----------------------------------------------------------------------
pubnub = Pubnub(publish_key, subscribe_key, secret_key, ssl_on)

pubnub.subscribe({
    'channel' : channel_name,
    'connect' : connected,
    'callback' : message_received
})

## -----------------------------------------------------------------------
## IO Event Loop
## -----------------------------------------------------------------------
try:
    pubnub.start()
except:
    pass
