from detect_pattern import detect_patterns
from deal_with_obfucate_code import obfuscate_detect


def IOC_detect(code):
    ioc_count = 0
    if code:
        # scan_result = VBA_Scanner(code).scan(True,True)
        scan_result = detect_patterns(code,True)
        if scan_result:
            return True

def is_high_weight_delimiter(code, pos):

    patterns = [
        "}\n", "End Sub\n", "]]>", "?>", "%>",

        "End Class\n", "End Class\r\n",

        "End Function\n", "End Function\r\n", 
        "End Sub\n", "End Sub\r\n",

        "End If\n", "End If\r\n", 
        "End While\n", "End While\r\n", 
        "End For\n", "End For\r\n", 
        "End Try\n", "End Try\r\n", 
        "End With\n", "End With\r\n",
        "Until\n", "Until\r\n", 
        "Loop\n", "Loop\r\n",
        "Next\n", "Next\r\n", 
        "Wend\n", "Wend\r\n",

        "]]>\n", "]]>\r\n", "?>\n", "?>\r\n", "%>\n", "%>\r\n", 
        "-->\n", "-->\r\n", "</script>\n", "</script>\r\n",
        "</style>\n", "</style>\r\n",

        "#END IF\n", "#END IF\r\n", 
        "#END REGION\n", "#END REGION\r\n",

        "END\n", "END\r\n"
        ]
    for pattern in patterns:
        if code[pos-len(pattern)+1:pos+1] == pattern:
            return True
    return False

def is_safe_delimiter(code, pos):
    if code[pos] in {' ', '\t', ',', ';', ':', '\n', '\r'}:
        left_safe = (pos == 0) or not code[pos-1].isalnum()
        right_safe = (pos == len(code)-1) or not code[pos+1].isalnum()
        return left_safe and right_safe
    return False

def split_macro(code, target):
    min_len=int(target*0.9)
    max_len=int(target*1.1)
    segments = []
    while len(code) > max_len:
        
        window_start = min(len(code), target)
        window_end = min(len(code), max_len)
        split_index = -1
        
        for pos in range(window_end, window_start - 1, -1):
            if is_high_weight_delimiter(code, pos):
                split_index = pos + 1  
                break
        
        if split_index == -1:
            for pos in range(window_end, window_start - 1, -1):
                # if code[pos] in {'\n', ';', '}'}:
                if code[pos] in {'\t', ')', ']', '}', '\n', '\r'}:
                    split_index = pos + 1
                    break
        

        if split_index == -1:
            for pos in range(window_end, 0, -1):
                if is_safe_delimiter(code, pos):  
                    split_index = pos
                    break
        

        if split_index == -1:
            split_index = max_len
        
        segments.append(code[:split_index])
        code = code[split_index:]
    

    if len(code) > 0:
        if len(segments) > 0 and len(code) < min_len:

            last_segment = segments[-1] + code
            if len(last_segment) <= max_len:
                segments[-1] = last_segment
            else:
                segments.append(code)
        else:
            segments.append(code)
    
    normal_segments = []
    ioc_score_10_segments = []
    score_20_segments = []
    segments_count = 0
    for i in segments:
        segments_count+=1
        _,score,IOC_label,_,_ = obfuscate_detect(i)
        if score>=6 and IOC_label == True:
            ioc_score_10_segments.append(i)
        elif score >=6 and IOC_label == False:
            score_20_segments.append(i)
        else:
            normal_segments.append(i)
    return normal_segments,ioc_score_10_segments,score_20_segments,segments_count