import re
import datetime
import time
import untangle


class OsccError:
    def __init__(self, platform_id_):
        self.platform_id = platform_id_

    def __str__(self):
        return self.platform_id

    def __repr__(self):
        return self.platform_id

    def extract_log(self, error_log):
        for line in error_log:
            match_src = re.findall(
                r"\|\sReference\sCode\s*:\s[0-9a-fA-F]+\s*\|",
                line, re.M | re.S)
            match_sev = re.findall(
                r"\|\sEvent\sSeverity\s*:\s[a-zA-Z\s]+\|", line, re.M | re.S)
            match_time = re.findall(
                r"\|\sCommitted\sat\s*:\s\d{2}\/\d{2}\/\d{4}\s\d{2}:\d{2}:\d{2}\s*\|",
                line, re.M | re.S)
            if match_src:
                match_src = match_src[0][29:37]
                self._src_e_id = match_src
            if match_sev:
                date = datetime.datetime.strptime(
                    match_time[0][29:48], "%m/%d/%Y %H:%M:%S")
                self._severity = match_sev[0][29:49]
                self._time_stamp = time.mktime(date.timetuple())

        found = re.findall(
            r"\|\s*Callout\sSection\s*\|.*?\n*\|-*\|\s*",
            error_log[0], re.M | re.S)

        if(len(found) != 0):
            self._callout_data = found[0]
        else:
            self._callout_data = None

        found = re.findall(
            r"\|-*\|\n*\|\s*User\sDefined\sData\s*\|\n*\|-*\|(?!.*\|-*\|\n*\|\s*User\sDefined\sData\s*\|\n*\|-*\|).*?\n*\|-*\|\n*\|\s*Manufacturing\sInformation\s*\|\n*\|-*\|",
            error_log[0], re.M | re.S)
        if len(found) == 0:
            found = re.findall(
                r"\|\s*OSCC\sCP\sSense\sInformation\s*\|.*?\n*\|-*\|\n*\|\s*User\sDefined\sData\s*\|",
                error_log[0], re.M | re.S)
        if len(found) == 0:
            found = re.findall(
                r"\|\s*OSCC\sCP\sSense\sInformation\s*\|.*?\n*\|-*\|", error_log[0], re.M | re.S)
        self.extract_usre_data(found)

    def extract_usre_data(self, user_data_list):
        user_data = ""
        for data in user_data_list:
            user_data += data + "\n"

        self._values = {}

        previous_key = ""
        continous_key_index = 1
        for line in user_data.split('\n'):
            line = line.rstrip()
            if ":" in line:
                key = line.split(":")
                if len(key) != 2:
                    new_key = key
                    key = key[0][2:]+"_"+key[2]
                    value = new_key[3][1:-2]
                else:
                    (key, value) = line.split(":")
                    key = key[2:]
                    value = value[1:-1]
                key = key.strip()
                value = value.strip()

                if(key == previous_key):
                    continous_key_index += 1
                    key += " " + str(continous_key_index)
                else:
                    previous_key = key
                    continous_key_index = 1

                if key not in self._values:
                    self._values[key] = value
                else:
                    count = 0
                    for each_key in self._values:
                        if (key + "_") in each_key:
                            count = count + 1
                    #To count the fist key, which will not have "_", add 1
                    count += 1
                    n_key = key + "_" + str(count)
                    self._values[n_key] = value

    def get_values(self, key, iter, type):
        if(iter == 0):
            str_value = self._values[key]
        else:
            new_key = key + "_" + str(iter)
            str_value = self._values[new_key]

        if(type == 's'):
            return str_value
        else:
            return int(str_value, 16)

    def analyze_rule(self, rule_node):
        self._found_error = False
        iter = 0
        while True:
            if(not self.statement_execute(rule_node, iter)):
                break
            iter += 1
        
        return self._found_error

    def statement_execute(self, rule_node, iter):
        Variable = {}
        for statement_node in rule_node.children:
            if(statement_node._name == "variable"):
                try:
                    Variable[statement_node["index"]] = self.get_values(
                        statement_node.cdata, iter,
                        statement_node["type"])
                except KeyError:
                    return False
            elif(statement_node._name == "evaluation"):
                Variable[statement_node["index"]] = eval(statement_node.cdata)
            elif(statement_node._name == "condition"):
                if(eval(statement_node.cdata) != True):
                    break
                else:
                    self._found_error = True
                    print("\n")
            elif(statement_node._name == "OutputPrint"):
                self.print_rule_output(statement_node, Variable)
            else:
                raise Exception("Unexpected token: " + statement_node._name)

        return True

    def print_rule_output(self, output_node, Variable):
        for line_node in output_node.children:
            if(line_node._name == "Line"):
                msg = ""
                for msg_node in line_node.children:
                    if(msg_node._name == "Message"):
                        msg += msg_node.cdata
                    elif(msg_node._name == "ValueIndex"):
                        if(type(Variable[msg_node.cdata]) == type("")):
                            msg += Variable[msg_node.cdata]
                        else:
                            msg += hex(Variable[msg_node.cdata])
                    else:
                        raise Exception("Unexpected token: " + msg_node._name)

                print(msg)
            else:
                raise Exception("Unexpected token: " + line_node._name)

    def print_callout(self):
        if(self._callout_data != None):

            #remove first three lines
            callout = '\n'.join(self._callout_data.split('\n')[3:])

            print("\nHW part/s to be replaced\n")
            print(callout)
