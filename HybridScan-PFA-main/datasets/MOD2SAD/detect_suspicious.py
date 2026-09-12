import re

SUSPICIOUS_KEYWORDS = {
    #http://www.certego.net/en/news/advanced-vba-macros/
    'May read system environment variables':
        ('Environ','Win32_Environment','Environment','ExpandEnvironmentStrings','HKCU\\Environment',
        'HKEY_CURRENT_USER\\Environment'),
    'May open a file':
        ('Open',),
    'May write to a file (if combined with Open)':
        ('Write', 'Put', 'Output', 'Print #'),
    'May read or write a binary file (if combined with Open)':
        ('Binary',),
    'May copy a file':
        ('FileCopy', 'CopyFile','CopyHere','CopyFolder'),
    'May move a file':
        ('MoveHere', 'MoveFile', 'MoveFolder'),
    'May delete a file':
        ('Kill',),
    'May create a text file':
        ('CreateTextFile', 'ADODB.Stream', 'WriteText', 'SaveToFile'),
    'May run an executable file or a system command':
        ('Shell', 'vbNormal', 'vbNormalFocus', 'vbHide', 'vbMinimizedFocus', 'vbMaximizedFocus', 'vbNormalNoFocus',
         'vbMinimizedNoFocus', 'WScript.Shell', 'Run', 'ShellExecute', 'ShellExecuteA', 'shell32','InvokeVerb','InvokeVerbEx',
         'DoIt'),
    'May run a dll':
        ('ControlPanelItem',),
    'May execute file or a system command through WMI':
        ('Create',),
    'May run an executable file or a system command on a Mac':
        ('MacScript','AppleScript'),
    'May run PowerShell commands':
        ('PowerShell', 'noexit', 'ExecutionPolicy', 'noprofile', 'command', 'EncodedCommand',
         'invoke-command', 'scriptblock', 'Invoke-Expression', 'AuthorizationManager'),
    'May run an executable file or a system command using PowerShell':
        ('Start-Process',),
    'May call a DLL using Excel 4 Macros (XLM/XLF)':
        ('CALL',),
    'May hide the application':
        ('Application.Visible', 'ShowWindow', 'SW_HIDE'),
    'May create a directory':
        ('MkDir',),
    'May save the current workbook':
        ('ActiveWorkbook.SaveAs',),
    'May change which directory contains files to open at startup':
        ('Application.AltStartupPath',),
    'May create an OLE object':
        ('CreateObject',),
    'May get an OLE object with a running instance':
        ('GetObject',),
    'May create an OLE object using PowerShell':
        ('New-Object',),
    'May run an application (if combined with CreateObject)':
        ('Shell.Application',),
    'May run an Excel 4 Macro (aka XLM/XLF) from VBA':
        ('ExecuteExcel4Macro',),
    'May enumerate application windows (if combined with Shell.Application object)':
        ('Windows', 'FindWindow'),
    'May run code from a DLL':
        ('Lib',),
    'May run code from a library on a Mac':
        ('libc.dylib', 'dylib'),
    'May inject code into another process':
        ('CreateThread', 'CreateUserThread', 'VirtualAlloc', 
        'VirtualAllocEx', 'RtlMoveMemory', 'WriteProcessMemory',
        'SetContextThread', 'QueueApcThread', 'WriteVirtualMemory', 'VirtualProtect',
        ),
    'May run a shellcode in memory':
        ('SetTimer',  
         ),
    'May download files from the Internet':
        ('URLDownloadToFileA', 'Msxml2.XMLHTTP', 'Microsoft.XMLHTTP',
         'MSXML2.ServerXMLHTTP', 
         'User-Agent', 
        ),
    'May download files from the Internet using PowerShell':
        ('Net.WebClient', 'DownloadFile', 'DownloadString'),
    'May control another application by simulating user keystrokes':
        ('SendKeys', 'AppActivate'),
    'May attempt to obfuscate malicious function calls':
        ('CallByName',),
    'May attempt to obfuscate specific strings (use option --deobf to deobfuscate)':
        ('Chr', 'ChrB', 'ChrW', 'StrReverse', 'Xor'),
    #Chr: http://msdn.microsoft.com/en-us/library/office/gg264465%28v=office.15%29.aspx
    'May read or write registry keys':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        ('RegOpenKeyExA', 'RegOpenKeyEx', 'RegCloseKey'),
    'May read registry keys':
    #sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        ('RegQueryValueExA', 'RegQueryValueEx',
         'RegRead',  #with Wscript.Shell
        ),
    'May detect virtualization':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
        (r'SYSTEM\ControlSet001\Services\Disk\Enum', 'VIRTUAL', 'VMWARE', 'VBOX'),
    'May detect Anubis Sandbox':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
    # NOTES: this sample also checks App.EXEName but that seems to be a bug, it works in VB6 but not in VBA
    # ref: http://www.syssec-project.eu/m/page-media/3/disarm-raid11.pdf
        ('GetVolumeInformationA', 'GetVolumeInformation',  # with kernel32.dll
         '1824245000', r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId',
         '76487-337-8429955-22614', 'andy', r'C:\exec\exec.exe', 'popupkiller'
         # note: removed 'sample' as it can trigger many false positives
        ),
    'May detect Sandboxie':
    # sample: https://malwr.com/analysis/M2NjZWNmMjA0YjVjNGVhYmJlZmFhNWY4NmQxZDllZTY/
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('SbieDll.dll', 'SandboxieControlWndClass'),
    'May detect Sunbelt Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        (r'C:\file.exe',),
    'May detect Norman Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('currentuser',),
    'May detect CW Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('Schmidti',),
    'May detect WinJail Sandbox':
    # ref: http://www.cplusplus.com/forum/windows/96874/
        ('Afx:400000:0',),
    'May attempt to disable VBA macro security and Protected View':
    # ref: http://blog.trendmicro.com/trendlabs-security-intelligence/qkg-filecoder-self-replicating-document-encrypting-ransomware/
    # ref: https://thehackernews.com/2017/11/ms-office-macro-malware.html
        ('AccessVBOM', 'VBAWarnings', 'ProtectedView', 'DisableAttachementsInPV', 'DisableInternetFilesInPV',
         'DisableUnsafeLocationsInPV', 'blockcontentexecutionfrominternet'),
    'May attempt to modify the VBA code (self-modification)':
        ('VBProject', 'VBComponents', 'CodeModule', 'AddFromString'),
    'May modify Excel 4 Macro formulas at runtime (XLM/XLF)':
        ('FORMULA.FILL',),
}

SUSPICIOUS_KEYWORDS_REGEX = {
    'May use Word Document Variables to store and hide data':
        (r'\.\s*Variables',),  
    'May run a shellcode in memory':
        (r'EnumSystemLanguageGroupsW?', 
         r'EnumDateFormats(?:W|(?:Ex){1,2})?', 
         ),
    'May run an executable file or a system command on a Mac (if combined with libc.dylib)':
        ('system', 'popen', r'exec[lv][ep]?'),
    'May run an executable file or a system command using Excel 4 Macros (XLM/XLF)':
        (r'(?<!Could contain following functions: )EXEC',),
    'Could contain a function that allows to run an executable file or a system command using Excel 4 Macros (XLM/XLF)':
        (r'Could contain following functions: EXEC',),
    'May call a DLL using Excel 4 Macros (XLM/XLF)':
        (r'(?<!Could contain following functions: )REGISTER',),
    'Could contain a function that allows to call a DLL using Excel 4 Macros (XLM/XLF)':
        (r'Could contain following functions: REGISTER',),
}


SUSPICIOUS_KEYWORDS_NOREGEX = {
    'May use special characters such as backspace to obfuscate code when printed on the console':
        ('\b',),
}

def detect_suspicious(vba_code, obfuscation=None):

    FALSE_POSITIVE_KEYWORDS = {
        'Document_Close', 'Workbook_BeforeClose', 
        'CreateTextFile', 'ADODB.Stream', 'SaveAs', 
        'Visible', 'Open', 'Write', 'Print',
        'SaveAs','File Operation','UI control',
        'http://schemas.microsoft.com/','XML Names'
    }

    #vba_code = vba_code.lower()
    results = []
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for description, keywords in SUSPICIOUS_KEYWORDS.items():
        for keyword in keywords:
            if keyword in FALSE_POSITIVE_KEYWORDS:
                continue
            match = re.search(r'(?i)\b' + re.escape(keyword) + r'\b', vba_code)
            if match:
                found_keyword = match.group()
                results.append((found_keyword, description + obf_text))
    for description, keywords in SUSPICIOUS_KEYWORDS_REGEX.items():
        for keyword in keywords:
            match = re.search(r'(?i)\b' + keyword + r'\b', vba_code)
            if match:
                found_keyword = match.group()
                results.append((found_keyword, description + obf_text))
    for description, keywords in SUSPICIOUS_KEYWORDS_NOREGEX.items():
        for keyword in keywords:
            if keyword.lower() in vba_code:
                if not(keyword=='\b' and obfuscation is not None):
                    results.append((keyword, description + obf_text))
    return results