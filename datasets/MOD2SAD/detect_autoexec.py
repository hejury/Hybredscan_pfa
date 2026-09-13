import re

AUTOEXEC_KEYWORDS = {
    # MS Word:
    'Runs when the Word document is opened':
        ('AutoExec', 'AutoOpen', 'DocumentOpen'),
    'Runs when the Word document is closed':
        ('AutoExit', 'AutoClose', 'Document_Close', 'DocumentBeforeClose'),
    'Runs when the Word document is modified':
        ('DocumentChange',),
    'Runs when a new Word document is created':
        ('AutoNew', 'Document_New', 'NewDocument'),

    'Runs when the Word or Publisher document is opened':
        ('Document_Open',),
    'Runs when the Publisher document is closed':
        ('Document_BeforeClose',),

    'Runs when the Excel Workbook is opened':
        ('Auto_Open', 'Workbook_Open', 'Workbook_Activate', 'Auto_Ope'),
    'Runs when the Excel Workbook is closed':
        ('Auto_Close', 'Workbook_Close', 'Workbook_BeforeClose'),
    'May run when an Excel WorkSheet is opened':
        ('Worksheet_Calculate',),
}


AUTOEXEC_KEYWORDS_REGEX = {
    'Runs when the file is opened (using InkPicture ActiveX object)':
        (r'\w+_Painted', r'\w+_Painting'),
    'Runs when the file is opened and ActiveX objects trigger events':
        (r'\w+_GotFocus', r'\w+_LostFocus', r'\w+_MouseHover', r'\w+_Click',
         r'\w+_Change', r'\w+_Resize', r'\w+_BeforeNavigate2', r'\w+_BeforeScriptExecute',
         r'\w+_DocumentComplete', r'\w+_DownloadBegin', r'\w+_DownloadComplete',
         r'\w+_FileDownload', r'\w+_NavigateComplete2', r'\w+_NavigateError',
         r'\w+_ProgressChange', r'\w+_PropertyChange', r'\w+_SetSecureLockIcon',
         r'\w+_StatusTextChange', r'\w+_TitleChange', r'\w+_MouseMove', r'\w+_MouseEnter',
         r'\w+_MouseLeave', r'\w+_Layout', r'\w+_OnConnecting', r'\w+_FollowHyperlink', r'\w+_ContentControlOnEnter'),
}

def detect_autoexec(vba_code, obfuscation=None):
    results = []
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for description, keywords in AUTOEXEC_KEYWORDS.items():
        for keyword in keywords:
            match = re.search(r'(?i)\b' + re.escape(keyword) + r'\b', vba_code)
            if match:
                found_keyword = match.group()
                results.append((found_keyword, description + obf_text))
    for description, keywords in AUTOEXEC_KEYWORDS_REGEX.items():
        for keyword in keywords:
            match = re.search(r'(?i)\b' + keyword + r'\b', vba_code)
            if match:
                found_keyword = match.group()
                results.append((found_keyword, description + obf_text))
    return results
