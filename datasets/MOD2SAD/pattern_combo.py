import re
from rules import risk_rules

auto_exec = 0
persistence = 0
sensitive_operation = 0
shell_download = 0
file_operation = 0
obfucation = 0
crypto = 0
high_risk_func = 0
medium_risk_func = 0
def combo_match(statement):
    global auto_exec
    global persistence
    global sensitive_operation
    global shell_download
    global file_operation
    global obfucation
    global crypto
    global high_risk_func
    global medium_risk_func
    for key, value in risk_rules.items():
        try:
            mal_keywords = value[0] 
            pattern = r'\b(?:' + '|'.join([re.escape(word) for word in mal_keywords]) + r')\b'
            if key =='auto_exec' and  re.search(pattern, statement,re.IGNORECASE):
                auto_exec+=1
            if key =='high_risk' and  re.search(pattern, statement,re.IGNORECASE):
                high_risk_func+=1
            if key =='persistence' and  re.search(pattern, statement,re.IGNORECASE):
                persistence+=1
            if key =='network_operation' and  re.search(pattern, statement,re.IGNORECASE):
                shell_download+=1
            if key =='sensitive_operation' and  re.search(pattern, statement,re.IGNORECASE):
                sensitive_operation+=1
            if key =='medium_risk' and  re.search(pattern, statement,re.IGNORECASE):
                medium_risk_func+=1
            if key == 'shell_download_combo' and re.search(pattern, statement,re.IGNORECASE):
                shell_download+=1
            if key =='obfuscation' and  re.search(pattern, statement,re.IGNORECASE):
                obfucation+=1
            if key =='file_operations' and  re.search(pattern, statement,re.IGNORECASE):
                file_operation+=1
            if key =='base64' and  re.search(pattern, statement,re.IGNORECASE):
                crypto+=1
        except Exception as e:
            print(f"Error processing statement: {e}")
    
    
    return {
        "auto_exec":auto_exec,
        "persistence":persistence,
        "sensitive_operation":sensitive_operation,
        "shell_download":shell_download,
        "obfucation":obfucation,
        "file_operation":file_operation,
        "crypto":crypto,
        "high_risk_func":high_risk_func,
        "medium_risk_func":medium_risk_func
    }

def pattern_combo(keywords,IOCs):
    for j in IOCs:
        for i in keywords:
            statement = f"{i} {j[1]}"
            pattern_static = combo_match(statement)
            # if pattern_static:
            #     print(f'statement:{statement}')
            #     continue
        # print(f"pattern_static:{pattern_static}")
        return pattern_static
                        