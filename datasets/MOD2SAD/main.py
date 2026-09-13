import sys
import types
import msoffcrypto
from msoffcrypto_crack import Crack
from code_type_detection import detect_language
from code_slicer import split_macro
from LLM_for_deobfucate import LLM_query
from file_list_maker import file_list_maker
from deal_with_obfucate_code import filter_vba_attribute,obfuscate_detect
from detect_autoexec import detect_autoexec
from detect_pattern import detect_patterns
from detect_suspicious import detect_suspicious
from rules import common_rules, obfucation_rules, shell_download_rules
from oletools.olevba import VBA_Parser, rtfobj,VBA_Scanner
from oletools.olevba import detect_patterns as ole_detect_patterns
from concurrent.futures import ThreadPoolExecutor, as_completed
from model.Model_train_and_evaluate import model_main
import csv
import re
import os
import time
from ollama_for_deobfucate import stream_querry_llm

A_FILES = []
B_FILES = []

all_deobfucate_time = 0
all_obfucate_code_count =0
all_completion_tokens = 0
all_total_tokens=0
all_prompt_tokens=0

# need_llm_to_deobfuscate_count =0
level_1_llm_count = 0
level_2_llm_count = 0
no_need_llm_to_deobfuscate_count = 0
code_length_0_count = 0

model_context = ''
global_vector_store = []

detect_vba_count = 0
detect_xlm_count = 0

executor = ThreadPoolExecutor(16)  # Adjust the number of threads based on the number of CPU cores
COMMON_RULES_PATTERN = {k:re.compile(re.escape(k),re.IGNORECASE)for k in common_rules }
OBFUCATION_RULES_PATTERN = {k:re.compile(re.escape(k),re.IGNORECASE)for k in obfucation_rules}

def IOC_record_level_2(result,file_path):
    label = file_path.split('\\')[6] 
    print("Start recording the IOC that Olevba cannot detect")
    family_name = file_path.split('\\')[7]
    folder_path = '.\\expriment_data' + '\\' + family_name
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    else:
        pass
    if label == 'benign':row = ['benign'] 
    else: row = [file_path.split('\\')[9]] 
    llm_file_path = os.path.join(folder_path,'only_llm_ioc.csv')
    with open(llm_file_path,'a',encoding='utf-8',newline='') as f:
        writer = csv.writer(f) 
        writer.writerow(row)
    EXE_ROW = ['EXE']
    URL_ROW = ['URL']
    IP_ROW =['IP']
    if result:
        for i in result[0]:
            if 'Executable file name' in i[0]:EXE_ROW.append(i[1])
            elif 'URL' in i [0]:URL_ROW.append(i[1])
            elif 'IPv4 address' in i [0]:IP_ROW.append(i[1])
    with open(llm_file_path,'a',encoding='utf-8',newline='') as f: 
        writer = csv.writer(f) 
        writer.writerow(EXE_ROW)
        writer.writerow(URL_ROW)
        writer.writerow(IP_ROW)

def IOC_record_for_compare(single_file_ioc_result_w_llm,single_file_ioc_result,file_path):
    print("Start recording the results of the IOC comparison.")
    label = file_path.split('\\')[6]
    family_name = file_path.split('\\')[7]
    folder_path = '.\\expriment_data' + '\\' + family_name
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    else:
        pass
    if label == 'benign':row = ['benign'] 
    else: row = [file_path.split('\\')[9]] 
    llm_file_path = os.path.join(folder_path,'llm_ioc.csv')
    file_path = os.path.join(folder_path,'no_llm_ioc.csv')
    with open(llm_file_path,'a',encoding='utf-8',newline='') as f:
        writer = csv.writer(f) 
        writer.writerow(row)
    with open(file_path,'a',encoding='utf-8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)
    
    EXE_ROW = ['EXE']
    URL_ROW = ['URL']
    IP_ROW =['IP']
    if single_file_ioc_result_w_llm:
        for i in single_file_ioc_result_w_llm[0]:
            if 'Executable file name' in i[0]:EXE_ROW.append(i[1])
            elif 'URL' in i [0]:URL_ROW.append(i[1])
            elif 'IPv4 address' in i [0]:IP_ROW.append(i[1])
    with open(llm_file_path,'a',encoding='utf-8',newline='') as f: 
        writer = csv.writer(f) 
        writer.writerow(EXE_ROW)
        writer.writerow(URL_ROW)
        writer.writerow(IP_ROW)

    EXE_ROW = ['EXE']
    URL_ROW = ['URL']
    IP_ROW =['IP']

    if single_file_ioc_result:
        for i in single_file_ioc_result[0]:
            if 'Executable file name' in i[0]:EXE_ROW.append(i[1])
            elif 'URL' in i [0]:URL_ROW.append(i[1])
            elif 'IPv4 address' in i [0]:IP_ROW.append(i[1])
    with open(file_path,'a',encoding='utf-8',newline='') as f: 
        writer = csv.writer(f) 
        writer.writerow(EXE_ROW)
        writer.writerow(URL_ROW)
        writer.writerow(IP_ROW)

def IOC_detect(code):
    ioc_count = 0
    if code:
        # scan_result = VBA_Scanner(code).scan(True,True)
        scan_result = ole_detect_patterns(code,True)
        if scan_result:
            for i in scan_result:
                # if i[0] == 'IOC':
                ioc_count += 1
    return ioc_count,scan_result

def featrue_extract(vba_code,need_ole_ob):
    all_featrue = (common_rules + ['IOC', 'obfucation', 'label'])
    single_vba_feature_count = {featrue: 0 for featrue in all_featrue}

    autoexec_function_name = detect_autoexec(vba_code, 'VBA expression')
    autoexec_count = 0
    for i in autoexec_function_name:
        autoexec_count += 1
    single_vba_feature_count['AutoExec'] += autoexec_count

    suspicious_function_name = detect_suspicious(vba_code, 'VBA expression')
    # print('suspicious_function_name:',suspicious_function_name)
    suspicious_count = 0
    for i in suspicious_function_name:
        suspicious_count += 1
    single_vba_feature_count['AutoExec'] += suspicious_count

    for keyword,pattern in COMMON_RULES_PATTERN.items():
        matches = pattern.findall(vba_code)
        single_vba_feature_count[keyword] += len(matches)
    
    if need_ole_ob:
        _,_,_,ob_count,ioc_result = obfuscate_detect(vba_code)
        single_vba_feature_count['obfucation'] += ob_count
    else:
        _,_,_,ob_count,ioc_result = obfuscate_detect(vba_code)
        single_vba_feature_count['obfucation'] = 0

    ioc_count=0
    for i in ioc_result:
        ioc_count+=1
    single_vba_feature_count['IOC'] += ioc_count

    return single_vba_feature_count,ioc_result

def labeling(feature_count, filepath):
    label = filepath.split('\\')[6]

    if label != 'benign':
        feature_count['label'] = 1

    return feature_count


def extract_feature(filepath, init_vba_feature_count):
    global all_deobfucate_time,all_completion_tokens,all_obfucate_code_count,all_total_tokens,all_prompt_tokens,level_1_llm_count,level_2_llm_count,no_need_llm_to_deobfuscate_count,code_length_0_count
    parser = VBA_Parser(filepath)
    code_type_count = {
        'powershell': 0, 'cmd': 0, 'javascript': 0,
        'vba': 0, 'python': 0, 'shellcode': 0,
        'c': 0, 'c++': 0
    }

    if parser:
        process_result = parser.extract_all_macros()
        if process_result:
            compare_result = []
            compare_result_llm = []
            solo_result_llm = []
            for i in process_result:
                single_macros = i[3]
                cleaned_code = filter_vba_attribute(single_macros)
                if len(cleaned_code) >0:
                    # obfuscate_label,score,IOC_label,ob_count = obfuscate_detect(cleaned_code)
                    print(f"Checking whether it is a corrupted code.")
                    obfuscate_label,_,_,ob_count,_ = obfuscate_detect(cleaned_code)
                    if obfuscate_label: 
                        level_1_deob_code = ''
                        level_2_deob_code =''
                        original_code = ''

                        llm_result_level_1=None
                        llm_result_level_2=None
                        compare_ioc=None

                        normal_single_vba_feature_count=None
                        level_1_single_vba_feature_count=None
                        level_2_single_vba_feature_count=None

                        model='deepseek-coder-v2:16b'
                        prompt = f'''You are a VBA macro disobfuscation expert. Follow the instruction and perform deep deobfuscation on the following obfuscated code:
                                        1. Perform all possible decoding operations :Base64, Hex, URL encoding, etc.
                                        2. Parse and perform string operations: concatenate, invert, split, replace, etc.
                                        3. Evaluate all resolvable expressions: mathematical, logical, and character encoding conversion (Chr/Asc).
                                        4. Apply XOR decryption to try to identify common keys.
                                        5. Remove redundant code, useless operation code and useless loops. 
                                        6. The parts of the code that cannot be unobfuscated or that you think are not obfuscated should be output as is. 
                                        7. Do not add any comments or explanatory text. 
                                        8. Keep the original code structure. 
                                        Obfuscated code:{i} 
                                        '''
                        normal_segments,ioc_score_10_segments,score_20_segments,segments_count = split_macro(cleaned_code,4088)
                        if segments_count >1: 
                            # llm_result_level_1=[]
                            # llm_result_level_2=[]
                            print(f"The code in level_0 has {len(normal_segments)} sections.")
                            if normal_segments:
                                print(f"The confusing code is divided into {segments_count} segments.")
                                need_ole_ob = False
                                normal_code = ''
                                for i in normal_segments:
                                    normal_code+=i
                                    no_need_llm_to_deobfuscate_count+=1                                    
                                normal_single_vba_feature_count,_= featrue_extract(normal_code,False)
                                normal_single_code_type = detect_language(normal_code)
                                code_type_count[normal_single_code_type] += 1
                                for key in normal_single_vba_feature_count:init_vba_feature_count[key] += normal_single_vba_feature_count[key]
                                init_vba_feature_count['obfucation'] = 0
                                init_vba_feature_count['obfucation'] +=ob_count
                            
                            if ioc_score_10_segments:
                                print(f"The code for level_1 consists of {len(ioc_score_10_segments)} segments.")
                                for i in ioc_score_10_segments:
                                    level_1_llm_count+=1
                                    llm_output,completion_tokens,prompt_tokens,total_tokens,deobfucate_time = stream_querry_llm(model,prompt)
                                    all_deobfucate_time+=deobfucate_time 
                                    all_obfucate_code_count+=1 
                                    all_completion_tokens+=completion_tokens
                                    all_total_tokens+=total_tokens 
                                    all_prompt_tokens+=prompt_tokens 
                                    level_1_deob_code+=llm_output 
                                    original_code +=i 
                                level_1_single_vba_feature_count,llm_result_level_1 = featrue_extract(level_1_deob_code,True)
                                # _,compare_ioc = featrue_extract(original_code,True)
                                _,compare_ioc = featrue_extract(original_code,True)
                                level_1_single_code_type = detect_language(level_1_deob_code)
                                code_type_count[level_1_single_code_type] += 1
                                if llm_result_level_1:compare_result_llm.append(llm_result_level_1) 
                                if compare_ioc:compare_result.append(compare_ioc)
                                for key in level_1_single_vba_feature_count:
                                    init_vba_feature_count[key] += level_1_single_vba_feature_count[key]

                            if score_20_segments:
                                print(f"The code for level_2 consists of {len(score_20_segments)} segments.")
                                for i in score_20_segments:
                                    level_2_llm_count+=1                
                                    llm_output,completion_tokens,prompt_tokens,total_tokens,deobfucate_time = stream_querry_llm(model,prompt) 
                                    all_obfucate_code_count+=1 
                                    all_completion_tokens+=completion_tokens 
                                    all_total_tokens+=total_tokens 
                                    all_prompt_tokens+=prompt_tokens 
                                    level_2_deob_code+=llm_output 
                                level_2_single_vba_feature_count,llm_result_level_2 = featrue_extract(level_2_deob_code,True)
                                level_2_single_code_type = detect_language(level_2_deob_code)
                                code_type_count[level_2_single_code_type] += 1
                                if llm_result_level_2:solo_result_llm.append(llm_result_level_2) 
                                for key in level_2_single_vba_feature_count:
                                    init_vba_feature_count[key] += level_2_single_vba_feature_count[key]
                        else: 
                            print("Single code snippet")
                            if normal_segments:
                                print("level_0")
                                no_need_llm_to_deobfuscate_count+=1
                                single_ob_code = normal_segments[0]
                                normal_single_vba_feature_count,_ = featrue_extract(single_ob_code,False)
                                normal_single_code_type = detect_language(single_ob_code)
                                code_type_count[normal_single_code_type] += 1
                                for key in normal_single_vba_feature_count:
                                    init_vba_feature_count[key] += normal_single_vba_feature_count[key]
                                init_vba_feature_count['obfucation'] = 0
                                init_vba_feature_count['obfucation'] +=ob_count
                            if ioc_score_10_segments:
                                print("level_1")
                                level_1_llm_count+=1
                                single_ob_code = ioc_score_10_segments[0]
                                llm_output,completion_tokens,prompt_tokens,total_tokens,deobfucate_time = stream_querry_llm(model,prompt)
                                all_deobfucate_time+=deobfucate_time
                                all_obfucate_code_count+=1 
                                all_completion_tokens+=completion_tokens 
                                all_total_tokens+=total_tokens 
                                all_prompt_tokens+=prompt_tokens 
                                level_1_deob_code+=llm_output 
                                original_code +=single_ob_code 
                                level_1_single_vba_feature_count,llm_result_level_1 = featrue_extract(level_1_deob_code,True)
                                _,compare_ioc = featrue_extract(original_code,True)
                                level_1_single_code_type = detect_language(level_1_deob_code)
                                code_type_count[level_1_single_code_type] += 1
                                for key in level_1_single_vba_feature_count:init_vba_feature_count[key] += level_1_single_vba_feature_count[key]
                                if llm_result_level_1:compare_result_llm.append(llm_result_level_1) 
                                if compare_ioc:compare_result.append(compare_ioc) 
                            if score_20_segments:
                                print("level_2")
                                level_2_llm_count+=1
                                single_ob_code = score_20_segments[0]
                                
                                llm_output,completion_tokens,prompt_tokens,total_tokens,deobfucate_time = stream_querry_llm(model,prompt)
                                all_deobfucate_time+=deobfucate_time
                                all_obfucate_code_count+=1
                                all_completion_tokens+=completion_tokens 
                                all_total_tokens+=total_tokens 
                                all_prompt_tokens+=prompt_tokens 
                                level_2_deob_code+=llm_output 
                                level_2_single_vba_feature_count,llm_result_level_2 = featrue_extract(level_2_deob_code,True)
                                level_2_single_code_type = detect_language(level_2_deob_code)
                                code_type_count[level_2_single_code_type] += 1
                                if llm_result_level_2: solo_result_llm.append(llm_result_level_2) 
                                for key in level_2_single_vba_feature_count: init_vba_feature_count[key] += level_2_single_vba_feature_count[key]
                            
                    else: 
                        print("Not confusing the code")
                        no_need_llm_to_deobfuscate_count+=1
                        single_vba_feature_count,_ = featrue_extract(cleaned_code,False)
                        single_code_type = detect_language(cleaned_code)
                        code_type_count[single_code_type] += 1
                        for key in single_vba_feature_count:init_vba_feature_count[key] += single_vba_feature_count[key]
                        init_vba_feature_count['obfucation'] = 0
                        init_vba_feature_count['obfucation'] +=ob_count

                else: # If the length of the macro code after processing is 0, then skip it.
                    continue

            if compare_result_llm or compare_result: IOC_record_for_compare(compare_result_llm,compare_result,filepath)    
            if solo_result_llm: IOC_record_level_2(solo_result_llm,filepath)
            
            rec_failed_file = None

        else:
            print(f"No macro was found, so it is impossible to perform the detection using the macro.")
            init_vba_feature_count = None
            rec_failed_file = filepath
    else:
        print(f"The parser is empty, so it cannot be detected through macros: {parser}")
        init_vba_feature_count = None
        rec_failed_file = filepath
    parser.close()
    print (f"-- -- -- -- -- -- - now for LLM solution confusion of level_1 code segment is {level_1_llm_count} - - - - - - - - - - - -")
    print (f"-- -- -- -- -- -- - now for LLM solution to confuse the level_2 code segment is {level_2_llm_count} - - - - - - - - - - - -")
    print (f"-- -- -- -- -- -- - now don't need solution to confuse the code segment is {no_need_llm_to_deobfuscate_count} - - - - - - - - - - - -")
    return init_vba_feature_count, rec_failed_file, code_type_count
    # return init_vba_feature_count,rec_failed_file

def analyze_file(filepath, init_vba_feature_count):
    with open(filepath, "rb") as f:
        try:
            office_file = msoffcrypto.OfficeFile(f)
            if office_file.is_encrypted():
                print(f"{filepath} is an encrypted file.")
                options = types.SimpleNamespace(
                    man=False,
                    passwordlist='',
                    extractpasswords='',
                    crackedpassword='',
                    rules=False,
                    password='infected',
                    output=''
                )
                password = Crack(filepath, options)
                # print(f"password:{password}")
                if password:
                    try:
                        print("Start cracking")
                        enc_file = msoffcrypto.OfficeFile(open(filepath, 'rb'))
                        enc_file.load_key(password=password)
                        dec_file_path = filepath.split('.')[0] + '_dec.' + filepath.split('.')[1]
                        enc_file.decrypt(open(dec_file_path, "wb"))
                        print(f"The cracking has been successfully completed and the result has been saved in {dec_file_path}")
                        init_vba_feature_count, rec_failed_file,code_type_count = extract_feature(dec_file_path,init_vba_feature_count)
                        os.remove(dec_file_path)  

                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = exc_tb.tb_frame.f_code.co_filename
                        lineno = exc_tb.tb_lineno
                        init_vba_feature_count = None
                        rec_failed_file = None
                        labled_featrue_count = None
                        code_type_count = None
                        print(f"After decryption, the file {e} still cannot be processed. Line {lineno}")
                else:
                    print("The cracking attempt failed and the password was not found.")
                    rec_failed_file = filepath
                    init_vba_feature_count = None
                    code_type_count = None
            else:
                # For unencrypted files
                try:
                    init_vba_feature_count, rec_failed_file,code_type_count = extract_feature(filepath,init_vba_feature_count)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = exc_tb.tb_frame.f_code.co_filename
                    lineno = exc_tb.tb_lineno
                    init_vba_feature_count = None
                    rec_failed_file = filepath
                    code_type_count = None
                    print(f"Error occurred at {e}, line {lineno}")
            if init_vba_feature_count:
                rec_failed_file = None
                labled_featrue_count = labeling(init_vba_feature_count, filepath)
                result = [
                    filepath,
                    labled_featrue_count,
                    code_type_count
                ]
            else:
                rec_failed_file = filepath
                labled_featrue_count = None
                code_type_count = None
                result = [
                    filepath,
                    labled_featrue_count,
                    code_type_count
                ]
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            lineno = exc_tb.tb_lineno
            print(f"Test failed: {e}, line {lineno}")
            labled_featrue_count = None
            rec_failed_file = filepath
            code_type_count=None
            code_length=0
            code_count=0
            obfuscate_score=0
            result = [
                    filepath,
                    labled_featrue_count,
                    code_type_count,
                    code_length,
                    code_count,
                    obfuscate_score
                ]
    f.close()

    return result, rec_failed_file

def analyze_generate(file_list, index):
    start_time = time.time()
    results = []
    rec_failed_files_list = []
    file_count = 0

    for items in file_list:
        for item in items:
            filepath = item['filepath']
            filename = item['filename']
            all_featrue = (common_rules + ['IOC', 'obfucation', 'label'])
            init_vba_feature_count = {featrue: 0 for featrue in all_featrue}

            result,rec_failed_file = analyze_file(filepath,init_vba_feature_count)
            if result and result[1]:
                results.append(result)
                file_count+=1
                print(f"The detection of the {file_count}th file is complete")
                if file_count%10==0:
                    print("Start writing the data")
                    Experiment_record(file_list, results, rec_failed_files_list, index,file_count)
                    results = []
            elif rec_failed_file:
                rec_failed_files_list.append(rec_failed_file)
        print("Start writing the remaining data")
        print(f"len(results):{len(results)}")
        Experiment_record(file_list, results, rec_failed_files_list, index,file_count)

    end_time = time.time()
    total_consuming_time = end_time - start_time
    print(f"Total consumption time: {total_consuming_time}")
    print(f"Average detection time per file: {(total_consuming_time / file_count)}")


def Experiment_record(file_list, results, rec_failed_files_list, index,file_count):
    print("Start generating training data")
    # all_featrue = (['filename'] + common_rules + ['IOC', 'obfucation','label'])
    all_featrue = (common_rules + ['IOC', 'obfucation', 'label'])
    init_vba_feature_count = {featrue:0 for featrue in all_featrue}
    data_name = f'train_data_{index}.csv'
    data_path = os.path.join('.\\expriment_data', data_name)
    featrue_names = list(init_vba_feature_count.keys())
    with open(data_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if file_count == 10: 
            writer.writerow(featrue_names) 
        for res in results:
            # file_count+=1 
            # row = ([res[0]] + list(res[1].values()))
            row = list(res[1].values())
            # print(f"row:{row}")
            writer.writerow(row)
    print(f"The training data generation is completed. The records have been saved to train_data_{index}.csv")

if __name__ == '__main__':
    path_list = ['folder name'] # The name of your malicious document folder 
    for i in path_list:
        base_path = f'The root directory path of your malicious document folder'
        file_list = []
        for root, dirs, files in os.walk(base_path):
            if root == base_path and dirs:
                for dir in dirs:
                    dir_path = root + '\\' + dir
                    if dir == 'benign':
                        file_list.append(file_list_maker(dir_path))
                    if dir =='malicious':
                        file_list.append(file_list_maker(dir_path))

        print("The transmission began.")
        analyze_generate(file_list, i)

    print(f"The average time for LLM to resolve confusion in a single code segment:{all_deobfucate_time/all_obfucate_code_count}")
    print(f"Average completion tokens per LLM code segment: {all_completion_tokens / all_obfucate_code_count}")
    print(f"Average prompt tokens per LLM code segment: {all_prompt_tokens / all_obfucate_code_count}")
    print(f"Average total tokens per LLM code segment: {all_total_tokens / all_obfucate_code_count}")
    print(f"Number of code segments that were de-obfuscated by LLM: {all_obfucate_code_count}")
    print(f"Number of de-obfuscated code segments at level 1: {level_1_llm_count}")
    print(f"Number of de-obfuscated code segments at level 2: {level_2_llm_count}")
    print(f"Total number of code segments requiring de-obfuscation by LLM: {level_1_llm_count + level_2_llm_count}")

    
    model_main(path_list)  # Call the function of the machine learning model
