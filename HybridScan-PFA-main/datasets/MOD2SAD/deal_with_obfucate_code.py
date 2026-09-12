from oletools.olevba import VBA_Parser,VBA_Scanner
import time
import os
import re
import csv
import math
from collections import Counter

c_count = 0
def ngram_entropy(text,n):
    tokens = list(text) 
    ngrams =  [''.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
    total = len(ngrams)
    counter = Counter(ngrams)
    entropy = 0.0
    
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p) 
    
    return entropy

def calculate_entropy(code):
    if not code:  
        return 0.0
    
    frequency = Counter(code)
    total_chars = len(code)
    
    entropy = 0.0
    for char_count in frequency.values():
        probability = char_count / total_chars
        entropy -= probability * math.log2(probability)
    
    return entropy

def filter_vba_attribute(vba_code):
    pattern = r'^\s*Attribute\s.*?$'
    lines = vba_code.split('\n')
    filtered_lines = []
    removable_attributes = {
        'VB_Name', 'VB_Base', 'VB_GlobalNameSpace', 
        'VB_Creatable', 'VB_PredeclaredId', 'VB_Exposed',
        'VB_TemplateDerived', 'VB_Customizable'
    }

    for line in lines:
        attr_match = re.match(r'^\s*Attribute\s+([^\s=]+)', line, re.IGNORECASE)
        
        if attr_match:
            attr_name = attr_match.group(1)

            if attr_name == 'VB_Control':
                filtered_lines.append(line)

            elif attr_name in removable_attributes:
                continue  
            else:
                filtered_lines.append(line)  
        else:
            filtered_lines.append(line) 
    
    filtered_code = '\n'.join(filtered_lines)
    filtered_code = re.sub(r'\n{3,}', '\n\n', filtered_code)  
    return filtered_code.strip()
def obfuscate_detect(code):
    global c_count
    obfuscate_label = False
    ob_count =0
    ioc_result = []
    # code = filter_vba_attribute(code)
    score = 0
    if len(code) >0:
        scan_result = VBA_Scanner(code).scan(True,True)
        obfucated_pattern = ['Hex String','Base64 String','Dridex String','VBA obfuscated Strings','IOC']
        IOC_label = False
        if scan_result:
            for i in scan_result:
                if i[0] == 'Suspicious':
                    if i[1] == 'Chr' or i[1] == 'Xor':
                        score +=1
                        ob_count+=1
                if i[0] == 'Hex String':
                    score += 1
                    ob_count+=1
                if i[0] == 'Base64 String':
                    score += 2
                    ob_count+=1
                if i[0] == 'Dridex String':
                    score += 5
                    ob_count+=1
                if i[0] == 'IOC':
                    IOC_label=True
                    # ioc_record = [i[0],i[1]]
                    ioc_record = [i[2],i[1]]
                    # print(f"i:{i}")
                    ioc_result.append(ioc_record)
                    # print(f"i:{i}")
                if i[0] =='VBA obfuscated Strings':
                    ob_count+=1
                # elif i[0] == 'VBA string':
                

    if score >=6 :
        obfuscate_label = True
    else:
        obfuscate_label = False
    
    return obfuscate_label,score,IOC_label,ob_count,ioc_result
