import re
import datetime
import time
import untangle

class OsccError:
    def __init__(self, platformid):
        self.plat_id = platformid
    
    def __str__(self):
        return self.plat_id
    
    def __repr__(self):
        return self.plat_id

    def ExtractLog(self, errorLog):
        for line in errorLog:
            match_src = re.findall(r"\|\sReference\sCode\s*:\s[0-9a-fA-F]+\s*\|",line,re.M|re.S)
            match_sev = re.findall(r"\|\sEvent\sSeverity\s*:\s[a-zA-Z\s]+\|",line,re.M|re.S)
            match_time = re.findall(r"\|\sCommitted\sat\s*:\s\d{2}\/\d{2}\/\d{4}\s\d{2}:\d{2}:\d{2}\s*\|",line,re.M|re.S)
            if match_src:
                #print(match)
                #print(len(match))
                match_src = match_src[0][29:37]
                self.src_eid = match_src
                #src_eid.update("%s"errid:match_src)
            if match_sev:
               date = datetime.datetime.strptime(match_time[0][29:48],"%m/%d/%Y %H:%M:%S")
               #print(date,time.mktime(date.timetuple()))
               self.severity = match_sev[0][29:49]
               self.time_stamp = time.mktime(date.timetuple())

        found = re.findall(r"\|-*\|\n*\|\s*User\sDefined\sData\s*\|\n*\|-*\|(?!.*\|-*\|\n*\|\s*User\sDefined\sData\s*\|\n*\|-*\|).*?\n*\|-*\|\n*\|\s*Manufacturing\sInformation\s*\|\n*\|-*\|",errorLog[0],re.M|re.S)
        #print(len(found))
        if len(found) == 0:
            found = re.findall(r"\|\s*OSCC\sCP\sSense\sInformation\s*\|.*?\n*\|-*\|\n*\|\s*User\sDefined\sData\s*\|",errorLog[0], re.M | re.S)
        #print(len(found))
        self.ExtractUsreData(found)
    
    def ExtractUsreData(self, userDataList):
        userData = ""
        for data in userDataList:
            userData += data + "\n"

        self.values = {}

        for line in userData.split('\n'):
            line = line.rstrip()
            if ":" in line:
                key = line.split(":")
                if len(key)!=2:
                    new_key = key
                    key = key[0][2:]+"_"+key[2]
                    value = new_key[3][1:-2]
                else:
                    (key,value) = line.split(":")
                    key = key[2:]
                    value = value[1:-1]
                key = key.strip()
                value = value.strip()
                #print(value)
                if key not in self.values:
                    self.values[key] = value
                else:
                    count = 0
                    for each_key in self.values:
                        if key in each_key:
                            count = count + 1
                    #print(count)
                    n_key = key + "_" + str(count)
                    #print(n_key)
                    self.values[n_key] = value
                    #print(errid+":"+n_key+":"+value)
    
    def GetValues(self, key, iter):
        if(iter == 0):
            return int(self.values[key], 16)
        else:
            nKey = key + "_" + str(iter)
            return int(self.values[nKey], 16)
    
    def AnalyzeRule(self, ruleNode):
        iter = 0
        while True:
            if(not self.StatementExecute(ruleNode, iter)):
                break
            iter += 1

    def StatementExecute(self, ruleNode, iter):
        Variable={}
        for statementNode in ruleNode.children:
            if(statementNode._name == "variable"):
                try:
                    Variable[statementNode["index"]] = self.GetValues(statementNode.cdata, iter)
                except KeyError:
                    return False
            elif(statementNode._name == "evaluation"):
                Variable[statementNode["index"]] = eval(statementNode.cdata)
            elif(statementNode._name == "condition"):
                if(eval(statementNode.cdata) != True):
                    break
                else:
                    print ruleNode["name"] + " detected in error " + self.plat_id
            elif(statementNode._name == "OutputPrint"):
                self.PrintRuleOutput(statementNode, Variable)
            else:
                raise Exception("Unexpected token: " + statementNode._name)

        return True

    def PrintRuleOutput(self, outputNode, Variable):
        for lineNode in outputNode.children:
            if(lineNode._name != "Line"):
                raise Exception("Unexpected token: " + lineNode._name)

            msg = ""
            for msgNode in lineNode.children:
                if(msgNode._name == "Message"):
                    msg += msgNode.cdata
                elif(msgNode._name == "ValueIndex"):
                    msg += hex(Variable[msgNode.cdata])
                else:
                    raise Exception("Unexpected token: " + msgNode._name)

            print msg