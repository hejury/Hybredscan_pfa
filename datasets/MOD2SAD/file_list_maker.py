import os 
import pyzipper
from concurrent.futures import ThreadPoolExecutor, as_completed


            
def deal_with_single_zip(file_path,extract_to,pwd):
    with pyzipper.AESZipFile(file_path) as zip_ref:
        zip_ref.extractall(path=extract_to,pwd=pwd.encode('utf-8'))
    print(f"[+] Compression completed: {file_path} -> {extract_to}")

def deal_with_all_zip(base_path,max_threads=16):
    zip_files = []
    for root, dirs, files in os.walk(base_path):
        if files:
            for file in files:
                if file.lower().endswith('.zip'):
                    file_path = root + '\\' + file
                    zip_files.append(file_path)
                    
    count = 0
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_task = {
            executor.submit(deal_with_single_zip(file_path,root,'infected')):file_path
            for file_path in zip_files
        }
        
        for future in as_completed(future_task):
            file_path = future_task[future]
            count += 1

    print(f"Successfully decompressed {count} zip files")

def file_list_maker(base_path):
    file_list = []
    count = 0
    for root, dirs, files in os.walk(base_path):
        if files:
            for file in files:
                # if (file.split('.'))[1] != 'zip':
                if '.zip' not in file:
                    count+=1
                    file_path = root + '\\' + file
                    record ={
                        'filepath': file_path,
                        'filename': file
                    }
                    # print(f"file_path:{file_path}")
                    file_list.append(record)
    print(base_path.split('\\')[6],":",f"There are {count} files in total.")
    return file_list

