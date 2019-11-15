#!/usr/bin/python

from __future__ import print_function

__author__ = ["ManojKiran Eda", "Rajees Rahman P P"]
__copyright__ = "Copyright 2019"
__credits__ = ["Manish Chowdary"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = ["ManojKiran Eda", "Rajees Rahman P P"]
__email__ = ["manojeda@in.ibm.com", "rajerpp1@in.ibm.com"]
__status__ = "Production"

import re
import threading
import itertools
import sys
import untangle
import argparse

import osccError

parser = argparse.ArgumentParser(
    description='Analyses the error log to determine the root cause of failure, \
        and displays the parts to be replaced')

group = parser.add_mutually_exclusive_group()
group.add_argument(
    '--ruleHelp',
    action='store_true',
    help='to print the help message on how to add custom rule')
group.add_argument(
    '--keyList',
    action='store_true',
    help='to print list of keys available in the oscc error log')
group.add_argument(
    '--errlEducation',
    action='store_true',
    help='to print the description of each keys available in the oscc error log')
group.add_argument(
    '--elog',
    metavar='ELOG_PATH',
    help='path to the error log file to be analyzed')

spin_flag = True
oscc_errors = []
rule_xml = None


def display_rule_help():
    print("\nRule XML Format: \n")

    with open("rule_xml_format.xml", 'r') as stream:
        print(stream.read())


def display_key_list():
    print("\nList of keys:\n")

    with open("key_list.txt", 'r') as stream:
        print(stream.read())


def display_error_log_help():
    print("\nClock error log help:\n")

    with open("error_log_help.txt", 'r') as stream:
        print(stream.read())


def spin_the_cursor():
    global spin_flag

    spinner = itertools.cycle(
        ['|', '/', '-', '\\', '|', '/', '-', '\\'])

    print("\n Parsing in progress, please wait.....", end='')
    while spin_flag:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')


def parse_err_log(errlog_path):
    global spin_flag, oscc_errors

    # Ignore the non-ascii characters while reading
    f = open(errlog_path, 'r', errors="ignore")
    start = True

    while True:
        line = f.readline()
        if(line.strip() == ""):
            if(start):
                # Skip all empty lines before starting of errorlist
                start = False
                continue
            else:
                # break if ther is any empty line, which indicates, list of error is completed.
                break

        match1 = re.search(
            r"\|\s0[xX][0-9a-fA-F]+\s\s*[0-9]*\/[0-9]*\/[0-9]*\s*[0-9]*:[0-9]*:[0-9]*\s*[a-zA-Z]*\s[a-zA-Z]*\s*[a-zA-Z]*\s*oscc\s*\|",
            line)
        match2 = re.search(
            r"\|\s0[xX][0-9a-fA-F]+\s\s*[0-9]*\/[0-9]*\/[0-9]*\s*[0-9]*:[0-9]*:[0-9]*\s*[a-zA-Z]*\s[a-zA-Z]*:\s[a-zA-Z]*\s*oscc\s*\|",
            line)
        if match1:
            oscc_errors.append(osccError.OsccError(line[2:12]))
        if match2:
            oscc_errors.append(osccError.OsccError(line[2:12]))

    oscc_errors.reverse()

    data = f.read()
    f.close()

    for err in oscc_errors:
        found = re.findall(
            r"\n*(\|\s*Platform\sEvent\sLog\s-\s"
            + re.escape(err.platform_id)
            + r"\s*\|.*?\nTRACEBUFFER:\sMixed\sbuffer)\n*",
            data, re.M | re.S)

        err.extract_log(found)

    spin_flag = False
    print("done")


def parse_rule_xml():
    global rule_xml
    with open("rules.xml", 'r') as stream:
        rule_xml = untangle.parse(stream)


def analyze_error():
    print("\n\n#####################   FAILURE ANALYSIS   #####################\n")

    detected_list = [False] * len(rule_xml.Rules.children)

    for err in oscc_errors:
        rule_counter = 0
        for childnode in rule_xml.Rules.children:
            if (childnode._name != "AnalyzeRules"):
                raise Exception("Unexpected token: " + childnode._name)
            
            if(detected_list[rule_counter] == False):
                detected_list[rule_counter] = err.analyze_rule(childnode)
            
            rule_counter += 1

    for err in oscc_errors:
        err.print_callout()


def parse_analyze_error_log(elog_path):
    thread1 = threading.Thread(target=spin_the_cursor)
    thread2 = threading.Thread(
        target=parse_err_log,
        kwargs={"errlog_path": elog_path})
    thread3 = threading.Thread(target=parse_rule_xml)

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()

    analyze_error()

    print("\n\nThanks for Using this Script, Have a Great Day !!\n")


if __name__ == '__main__':
    args = parser.parse_args()

    if(args.ruleHelp):
        display_rule_help()
    elif(args.keyList):
        display_key_list()
    elif(args.errlEducation):
        display_error_log_help()
    else:
        parse_analyze_error_log(args.elog)
