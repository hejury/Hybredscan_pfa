import re

shell_download_rules = [
        r'Shell*?URLDownloadToFile', r'WScript\.Shell.*?\.Download',
]

obfucation_rules = [
        r"Left$\d+$", r"Right$\d+$", r"Mid$\d+$", "Split", 
        r"ChrW$.*?$", r'&H$".*?"$', r'Chr$\d+$', 
        r'StrReverse$".*?"$', r'Execute$', r'ExecuteGlobal$',
        'Evaluate', r'Application.Evaluate$', r'Eval$'
]

common_rules = [
    'ShellExecute',r'WinHttp\.WinHttpRequest\.','ADODB.Stream', 
    'WinHttpRequest', 'WebClient', 'DownloadFile', 
    'HTTPRequest', 'Shell', 'WScript.Shell', 
    '.Exec', 'CreateObject', 'ActiveXObject',
    'Execute', 'ExecuteGlobal', 'Eval', 
    'CallByName', 'GetObject','Shell.Application', 
    'NameSpace', 'CopyHere', 'MoveHere', 
    'RegWrite','HKEY_CURRENT_USER', 'SaveSetting', 
    'FileCopy', 'CopyFile', 'RegRead',
    'GetSetting', 'AppActivate','PutInClipboard', 
    'GetFromClipboard', 'SendKeys','CryptAcquireContext', 
    'CryptDecrypt',r'Environ\$?', 'WScript.Network', 
    'Network', 'DeCode', 'DecryptString', 
    'XORDecrypt','ExecQuery', 
    'winmgmts', 'Dir', 'GetFile', 
    'GetFolder','FileSystemObject', 'FSO', 
    'DriveExists', 'FolderExists','CreateTextFile', 
    'OpenTextFile','MoveFile','CreateFolder', 
    'Put', 'Get','MSXML2.XMLHTTP', 
    'Microsoft.XMLHTTP', 'MSXML2.ServerXMLHTTP','ADODB.Connection', 
    'ADODB.Recordset','Kill', 'RmDir', 
    'DeleteFile', 'DeleteFolder','Auto_Open', 
    'Document_Open', 'Workbook_Open', 'AutoExec', 
    'AutoNew','powershell',r'cmd\s*\/[ck]',
    'auto_close','document_close','workbook_close'
]
