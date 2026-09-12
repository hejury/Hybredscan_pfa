import re


SCHEME = r'\b(?:http|ftp)s?'

TLD = r'(?:xn--[a-zA-Z0-9]{4,20}|[a-zA-Z]{2,20})'
DNS_NAME = r'(?:[a-zA-Z0-9\-\.]+\.' + TLD + ')'

NUMBER_0_255 = r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'
IPv4 = r'(?:' + NUMBER_0_255 + r'\.){3}' + NUMBER_0_255
SERVER = r'(?:' + IPv4 + '|' + DNS_NAME + ')'
PORT = r'(?:\:[0-9]{1,5})?'
SERVER_PORT = SERVER + PORT
URL_PATH = r'(?:/[a-zA-Z0-9\-\._\?\,\'/\\\+&%\$#\=~]*)?'  # [^\.\,\)\(\s"]
URL_RE = SCHEME + r'\://' + SERVER_PORT + URL_PATH
re_url = re.compile(URL_RE)

EXCLUDE_URLS_PATTERNS = ["http://schemas.openxmlformats.org/",
                         "http://schemas.microsoft.com/",
                         "http://www.w3.org/", 
                         "https://xmlfileformat/",
                         "http://excel.templates" ,
                         "http://office.microsoft.com/" ,
                         r"http://schemas\.microsoft\.com/.*",
                         r"https://xmlfileformat/.*",
                         r"\.update\.microsoft\.com"
                         ]

RE_PATTERNS = (
    ('URL', re.compile(URL_RE)),
    ('IPv4 address', re.compile(IPv4)),
    ('E-mail address', re.compile(r'(?i)\b[A-Z0-9._%+-]+@' + SERVER + '\b')),
    ("Executable file name", re.compile(
        r"(?i)\b\w+\.(EXE|PIF|GADGET|MSI|MSP|MSC|VBS|VBE|VB|JSE|JS|WSF|WSC|WSH|WS|BAT|CMD|DLL|SCR|HTA|CPL|CLASS|JAR|PS1XML|PS1|PS2XML|PS2|PSC1|PSC2|SCF|LNK|INF|REG)\b")),
)

def detect_patterns(vba_code, obfuscation=None):
    results = []
    found = set()
    obf_text = ''
    if obfuscation:
        obf_text = ' (obfuscation: %s)' % obfuscation
    for pattern_type, pattern_re in RE_PATTERNS:
        for match in pattern_re.finditer(vba_code): 
            value = match.group()
            exclude_pattern_found = False
            for url_exclude_pattern in EXCLUDE_URLS_PATTERNS:
                if value.startswith(url_exclude_pattern):
                    exclude_pattern_found = True
            if value not in found and not exclude_pattern_found:
                # results.append((pattern_type + obf_text, value))
                results.append((pattern_type,value))
                found.add(value)
    return results