#!/usr/bin/python

from __future__ import print_function
from collections import OrderedDict
#import yaml
import fileinput
import re
import operator
import threading
import json
import itertools
import sys
import untangle
import binascii

import osccError


__author__ = "ManojKiran Eda"
__copyright__ = "Copyright 2019, OSCC Stretch Project"
__credits__ = ["Manish Chowdary"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "ManojKiran Eda"
__email__ = "manojeda@in.ibm.com"
__status__ = "Production"

verbose_level = 5

tokens_for_card_rule = ["register1","register2","operation","meaning"]
tokens_for_register_rule = ["name","type","bit","bitvalue","operation","interpretation"]
token_type_list = ["crc","pll","proc"]
token_valid_operation = ["eq","neq"]
token_valid_control_type = ["use_osc","osc_switch_control"]
tokens_for_direct_rule = ["name"]

CRED = '\033[91m'
CBLUE = '\033[96m'
CEND = '\033[0m'
debug = 0
spin = True
parse_done = True
oscc_errors = []
errorDict = OrderedDict()
spinner = itertools.cycle(['|', '/', '-', '\\','|','/','-','\\'])
errlog_path ="errlog.txt"
ruleXml = None

def my_print(verbose, message):
    if(verbose <= verbose_level):
        print(message)

def spin_the_cursor():
    global spin
    print("\n Parsing in progress, please wait.....",end='')
    while spin:
        sys.stdout.write(spinner.next())
        sys.stdout.flush()
        #time.sleep(0.05)
        sys.stdout.write('\b')


def find_node_for_failover(string,failed_card_string):
    #print(string)
    node_0 = [0,"0x00000010","0x00000011"]
    node_1 = [1,"0x00000020","0x00000021"]
    node_2 = [2,"0x00000030","0x00000031"]
    node_3 = [3,"0x00000040","0x00000041"]

    if string in node_0:
        if failed_card_string == "0x00000010":
            slotid = "0x00000010"
        else:
            slotid = "0x00000011"
        failure_node = node_0[0],
    elif string in node_1:
        if failed_card_string == "0x00000010":
            slotid = "0x00000020"
        else:
            slotid = "0x00000021"
        failure_node = node_1[0]
    elif string in node_2:
        if failed_card_string == "0x00000010":
            slotid = "0x00000030"
        else:
            slotid = "0x00000031"
        failure_node= node_2[0]
    else:
        if failed_card_string == "0x00000010":
            slotid = "0x00000040"
        else:
            slotid = "0x00000041"
        failre_node= node_3[0]
    return failure_node,slotid

def parse_err_log():
    global spin,parse_done, oscc_errors, my_dict,src_eid

    f = open(errlog_path, 'r')
    start = True

    while True:
        line = f.readline()
        if(line.strip() == ""):
            if(start):
                #Skip all empty lines before starting of errorlist
                start = False
                continue
            else:
                #break if ther is any empty line, which indicates, list of error is completed.
                break

        match1 = re.search(r"\|\s0[xX][0-9a-fA-F]+\s\s*[0-9]*\/[0-9]*\/[0-9]*\s*[0-9]*:[0-9]*:[0-9]*\s*[a-zA-Z]*\s[a-zA-Z]*\s*[a-zA-Z]*\s*oscc\s*\|",line)
        match2 = re.search(r"\|\s0[xX][0-9a-fA-F]+\s\s*[0-9]*\/[0-9]*\/[0-9]*\s*[0-9]*:[0-9]*:[0-9]*\s*[a-zA-Z]*\s[a-zA-Z]*:\s[a-zA-Z]*\s*oscc\s*\|",line)
        if match1:
            oscc_errors.append(osccError.OsccError(line[2:12]))
        if match2:
            oscc_errors.append(osccError.OsccError(line[2:12]))
        #print (platformid)
    
    oscc_errors.reverse()

    #print(platformid)
    data = f.read()
    f.close()

    time_stamp = []

    for err in oscc_errors:
        #Creating dictionary with platform id as key.
        errorDict[err.plat_id] = err

        found = re.findall(r"\n*(\|\s*Platform\sEvent\sLog\s-\s" +re.escape(err.plat_id)+ r"\s*\|.*?\nTRACEBUFFER:\sMixed\sbuffer)\n*",data, re.M | re.S)
        #print(type(found))
        
        err.ExtractLog(found)
    
    spin = False
    print(spin)
    #print(my_dict)
    #print(json.dumps(my_dict,sort_keys=True,indent=4))
    spin = False
    print("done")

def ParseRuleXml():
    global ruleXml
    with open("rules.xml", 'r') as stream:
        ruleXml = untangle.parse(stream)

def AnalyzeError():
    print("\n\n#####################   FAILURE ANALYSIS   #####################\n")

    for childnode in ruleXml.Rules.children:
        if (childnode._name != "AnalyzeRules"):
            raise Exception("Unexpected token: " + childnode._name)

        for err in oscc_errors:
            err.AnalyzeRule(childnode)

if __name__ == '__main__':
    #print(spin)
    thread1 = threading.Thread(target=spin_the_cursor)
    thread2 = threading.Thread(target=parse_err_log)
    thread3 = threading.Thread(target=ParseRuleXml)

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

    AnalyzeError()

    print("\n\nThanks for Using this Script, Have a Great Day !!\n")
