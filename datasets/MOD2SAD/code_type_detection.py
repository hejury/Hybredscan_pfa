import re
powershell_pattern=r'''(?ix)(?:
    (?:Invoke\-Expression|IEX|\bDownload(?:File|String)\b|\bFromBase64String\b|
    \bNet\.WebClient\b|\bSystem\.Net\.WebClient\b|Start-BitsTransfer|
    \bNew-Object\b|\bExpand-String\b)
    
    |\-(?:nop|noprofile|w|windowstyle|executionpolicy|e|enc|encodedcommand)\b

    |\.(?:DownloadData|DownloadFile|DownloadString|OpenRead|ReadToEnd|ResponseStream)
    

    #|(?:`["']|\s+[+&]\s+|['"]\s*&\s*['"]|\s{2,}) 
    |(?:powershell|iex)\s*['"]?\s*[+&]\s*['"]?\w+  
    |\$(?:env|shellid)\w*  
    

    |(?:http|https|ftp|tcp)://\S+  
    |[A-Za-z0-9+/=]{50,}  
    
    |\bAdd-Type\b|\b[Pp]owershell\.exe\b|\b-Command\b
    )'''

CMD_or_Batch_pattern = r'''(?ix)(?:
    
    \b(?:cmd\.exe|command\.com|cmd\s+/[ck]|start\s+/min|schtasks|
    bitsadmin|certutil|reg\s+(?:add|delete|copy)|wmic|
    taskkill|net\s+(?:use|user|group)|fsutil|vssadmin|
    copy|move|del|rd|mkdir|echo|set\s+\w+=)
    
    
    |\/(?:c|k|s|q|f|i|y|min)\b
    
   
    |\b(?:%[Tt][Ee][Mm][Pp]%|%[Aa][Pp][Pp][Dd][Aa][Tt][Aa]%|%[Ww][Ii][Nn][Dd][Ii][Rr]%|
    \\[Ww][Ii][Nn][Dd][Oo][Ww][Ss]\\[Ss][Yy][Ss][Tt][Ee][Mm]32\\)\b
    
    
    |\.(?:bat|cmd|exe|dll|vbs|js)\b
    
    
    |certutil\s+(?: -?decode | -?encode | -urlcache )
    |bitsadmin\s+/transfer\s+
    |reg\s+add\s+HK(?:LM|CU)\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    
    
    |\^(?:.|[xX][0-9a-fA-F]{2}) 
    |%\s?~\s?[0-9a-fA-F]+\s?%    
)'''

JavaScript_pattern = r'''(?ix)(?:

    \b(?:WScript\.Shell|ActiveXObject|Scripting\.FileSystemObject|
    MSXML2\.XMLHTTP|ADODB\.Stream|WinHttp\.WinHttpRequest|
    Shell\.Application)\b
    

    |\.(?:Run|Exec|CreateObject|Open|Send|SaveToFile|Load|
    response(?:Body|Text|Stream)|Write|WriteLine|eval|Execute)
    

    |\bnew\s+ActiveXObject\s*\(
    |\b(?:var|let|const)\s+\w+\s*=\s*new\s+\w+
    |\bwhile\s*\(true\)\s*\{\}  
    

    |(?:\\x[0-9a-fA-F]{2}|%[0-9a-fA-F]{2}){5,}  
    |String\.fromCharCode\((?:\d+,){5,}          
    |\/(?:[^/]|\\\/)+\/[gmi]{0,3}\.exec\s*\(     

    |\.(?:js|jse|wsf|wsh|hta)\b
)
'''

VBScript_patterns = r'''(?ix)(?:
    
    \b(?:CreateObject|WScript\.(?:Shell|CreateObject)|Scripting\.FileSystemObject|
    MSXML2\.XMLHTTP|ADODB\.Stream|WinHttp\.WinHttpRequest)\b
    
    
    |\.(?:Run|Exec|Open|Send|SaveToFile|Load|responseBody|Write|WriteLine|
    Execute|Eval|CreateTextFile|CopyFile|DeleteFile|GetSpecialFolder)
    
   
    |\b(?:Dim|Set|Call|Sub|Function|End\s+\w+|On\s+Error\s+Resume\s+Next)\b
    
    
    |GetObject\s*\(\s*"winmgmts:"
    |\b(?:chr|chrw)\(\d+\)
    |&\s*[hH][0-9a-fA-F]{2,}\b  
    
    
    |Execute\s*(?:Global)?\s*\(\s*"[\s\S]{50,}"\s*\)  
    |'[^'\n]{50,}  
    
    
    |\.(?:vbs|vbe|wsf|wsh|hta)\b
)
'''

Python_pattern = r'''(?ix)(?:
    \b(?:import\s+(?:os|sys|subprocess|ctypes|urllib\.request|base64|socket|
    __import__|importlib)|from\s+\w+\s+import)\b
    
  
    |\.(?:system|popen|call|run|check_output|urlopen|urlretrieve|b64decode|
    b64encode|windll|cdll|create_string_buffer|byref|eval|exec|compile|
    open|read|write|close|connect|send|recv|bind|listen|accept)
    
    
    |\b(?:def\s+\w+\s*\(|class\s+\w+|try:|except\s+\w+:|finally:|with\s+open)
    
    
    |subprocess\.Popen\([^)]*shell=True
    |ctypes\.windll\.kernel32\.
    |__import__\s*\(\s*['"]\w+['"]\s*\)
    
    
    |\b(?:getattr|setattr|__getattribute__|__import__)\(
    |\b(?:lambda|map|filter|reduce|functools)\.?
    |\beval\(.*?\)\s*\(  # 双重eval
    
    
    |\.(?:py|pyw|pyc|pyd)\b
)
'''

Shellcode_pattern = r'''(?ix)(?:
    
    \b(?:VirtualAlloc|VirtualProtect|VirtualFree|CreateThread|CreateProcess|
    WriteProcessMemory|ReadProcessMemory|RtlMoveMemory|LoadLibrary|GetProcAddress|
    OpenProcess|HeapCreate|HeapAlloc|EnumProcesses|CreateToolhelp32Snapshot|
    Process32First|Process32Next|TerminateProcess)\b
    
   
    |\b(?:MEM_COMMIT|MEM_RESERVE|PAGE_EXECUTE_READWRITE|PROCESS_ALL_ACCESS)\b
    
    
    |(?:\\x[0-9a-fA-F]{2}){20,}  
    |\b0x[0-9a-fA-F]{8}\b        
    |[0-9A-F]{2}\s+[0-9A-F]{2}\s+[0-9A-F]{2}  
    
    
    |\b(?:NtCreateThreadEx|ZwCreateThreadEx|RtlCreateUserThread|QueueUserAPC)\b
    
    
    |\b(?:STARTUPINFO|PROCESS_INFORMATION|CONTEXT|MEMORY_BASIC_INFORMATION)\b
    
    
    |\b(?:IsDebuggerPresent|CheckRemoteDebuggerPresent|OutputDebugString)\b
)
'''

Obfucation_pattern = r'''(?ix)(?:

    (?:[A-Za-z0-9+/=]{50,}|%[0-9a-fA-F]{2}|\\x[0-9a-fA-F]{2}|&#x[0-9a-fA-F]{2};){5,}
    

    |(?:strReverse|StrReverse|reverse|split|join|replace|substring|slice)\s*\(
    

    |function\s+[a-z]\s*\(\)\s*\{\s*return\s*[^;]{50,}\s*;\s*\}
    

    |(?:var|dim|set)\s+\w+\s*=\s*\d+\s*;\s*(?:\w+\s*=\s*\w+\s*[+\-*/]\s*\d+\s*;){5,}
    

    |\b(?:Environ|Environment\.GetEnvironmentVariable)\s*\(\s*["'][A-Za-z_]+["']\s*\)
    

    |["'](?:\\.|[^\\"']){100,}["']
)
'''

C_code_patterns = r'''(?ix)(?:

    /\#\s*(?:include|define|ifdef|ifndef|endif|pragma)\b
    

    \b(?:fopen|fclose|fread|fwrite|system|exec[lv]?[ep]?|popen|pclose|
    malloc|calloc|realloc|free|memset|memcpy|memmove|strcpy|strncpy|strcat|
    strncat|sprintf|snprintf|vsprintf|getenv|putenv|setenv|unsetenv|
    socket|connect|bind|listen|accept|send|recv|gethostbyname|inet_addr)\b
    

    |\b(?:CreateProcess[AW]?|ShellExecute[AW]?|WinExec|LoadLibrary[AW]?|
    GetProcAddress|VirtualAlloc|VirtualFree|VirtualProtect|WriteProcessMemory|
    CreateThread|WaitForSingleObject|CreateFile[AW]?|ReadFile|WriteFile|
    RegOpenKeyEx[AW]?|RegSetValueEx[AW]?|RegQueryValueEx[AW]?|WSAStartup)\b
    

    |\b(?:void\s*\*\s*\w+|\w+\s*\*\s*\w+|\w+\s*=\s*&\w+|\w+\s*->\s*\w+)
    

    |\b(?:memset\s*\([^,]+,\s*0x[0-9a-fA-F]+|memcpy\s*\([^,]+,\s*\w+,\s*sizeof\s*\(\w+\)\))
    

    |\b(?:struct\s+sockaddr_in|htons|htonl|ntohs|ntohl|INADDR_ANY|AF_INET|SOCK_STREAM)
    

    |\b(?:Shellcode|payload|inject|malicious|exploit)\b
    |0x[0-9a-fA-F]{8}\s*//\s*(?:address|pointer)
    

    |\b(?:\#define\s+\w+\s+\d+\s*\\?|/\*[^*]{50,}\*/)
    |\btypedef\s+(?:struct|union|enum)\s*\{\s*[^}]{50,}\s*\}\s*\w+\s*;
    

    |\.(?:c|h|o|obj|dll|so|a|lib)\b
)
'''

C_Plus_patterns = r'''(?ix)(?:

    \b(?:class\s+\w+|template\s*<|public\s*:|private\s*:|protected\s*:|virtual\s+\w+|
    namespace\s+\w+|using\s+namespace|new\s+\w+\[\]|delete\s*\[\]|try|catch\s*\(|
    throw|typeid|dynamic_cast|static_cast|reinterpret_cast|const_cast|
    mutable|explicit|friend|operator\s*[+\-*/%&|\^<>!=]=?|this|nullptr)\b
    

    \b(?:std\s*::\s*(?:vector|list|map|set|string|wstring|basic_string|cout|cin|cerr|
    unique_ptr|shared_ptr|make_shared|make_unique|function|bind|regex|match_results|
    for_each|transform|copy|sort|find|accumulate|thread|mutex|lock_guard|async|future))\b
    

    |\b(?:CoInitialize|CoCreateInstance|CoUninitialize|CComPtr|CComQIPtr|
    _bstr_t|_variant_t|SysAllocString|SysFreeString|IUnknown|IDispatch)\b
    

    |\b(?:malware|ransomware|keylogger|rootkit|botnet|backdoor)\b
    |\bstd\s*::\s*this_thread\s*::\s*sleep_for\s*\(
    |\bCreateRemoteThread\s*\(
    

    |\b(?:VirtualAllocEx|WriteProcessMemory|CreateRemoteThread|QueueUserAPC|NtCreateThreadEx)\b
    |\b(?:HOOKPROC|SetWindowsHookEx|UnhookWindowsHookEx|CallNextHookEx)\b
    

    |\b(?:\#define\s+\w+\s+\w+\(\)\s+\w+|template\s*<.*?>\s*class\s+\w+\s*{\s*[^}]{50,}\s*})
    |\b(?:__asm\s*\{[^}]*\}|__declspec\s*\([^)]*\))
    

    |\b(?:constexpr|noexcept|override|final|decltype|auto\s*[=:])
    |\b(?:lambda\s*\[[^\]]*\]\s*\([^)]*\)\s*\{[^}]*\})

    |\.(?:cpp|cxx|cc|hpp|hxx|hh|dll|exe|pdb|ilk)\b
)

'''

def detect_language(code):    
    patterns = {
        "powershell":powershell_pattern,
        "cmd":CMD_or_Batch_pattern,
        "javascript":JavaScript_pattern,
        "vba":VBScript_patterns,
        "python":Python_pattern,
        "shellcode":Shellcode_pattern,
        "c":C_code_patterns,
        "c++":C_Plus_patterns,
    }
    # print(f"code:{code}")

    scores = {lang: len(re.findall(pattern, code)) for lang, pattern in patterns.items()}
    # for lang, pattern in patterns.items():
        # result = re.findall(pattern, code)
        # print(f"{lang}:{result}")
    code_type= max(scores, key=scores.get) if max(scores.values()) > 0 else "vba"
    # print(f"type:{type}")
    return code_type
