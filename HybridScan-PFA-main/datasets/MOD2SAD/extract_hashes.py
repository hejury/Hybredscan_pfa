import os
import hashlib

def get_sha256(file_path):
    """
    计算文件的 SHA-256 哈希值。
    采用分块读取，防止单个样本过大导致内存溢出。
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # 每次读取 4KB
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[-] 无法读取文件 {file_path}: {e}")
        return None

def main():
    # 基于你截图中的绝对路径
    base_dir = r"F:\科研文献撰写\基于LLM解混淆的Office检测框架\Samples\test_sample\S-A-1"
    
    benign_dir = os.path.join(base_dir, "benign")
    malicious_dir = os.path.join(base_dir, "malicious")
    
    # 创建一个专属文件夹来存放所有生成的 hash 列表
    output_dir = os.path.join(base_dir, "Hash_Manifests")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("[*] 开始处理 benign (良性) 样本...")
    if os.path.exists(benign_dir):
        benign_output_file = os.path.join(output_dir, "benign.txt")
        benign_hashes = []
        
        # 提取 Hash 并存入列表
        for filename in os.listdir(benign_dir):
            file_path = os.path.join(benign_dir, filename)
            if os.path.isfile(file_path):
                file_hash = get_sha256(file_path)
                if file_hash:
                    benign_hashes.append(file_hash)
        
        # 写入文件：顶部写入总数，随后写入 Hash
        with open(benign_output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"Total: {len(benign_hashes)}\n")
            for h in benign_hashes:
                out_f.write(f"{h}\n")
                
        print(f"[+] 良性样本处理完毕！共提取 {len(benign_hashes)} 个样本 -> benign.txt")
    else:
        print("[-] 未找到 benign 目录，请检查路径。")

    print("\n[*] 开始处理 malicious (恶意) 样本...")
    if os.path.exists(malicious_dir):
        # 遍历第一层：家族 (Family)
        for family in os.listdir(malicious_dir):
            family_path = os.path.join(malicious_dir, family)
            if not os.path.isdir(family_path):
                continue
            
            # 遍历第二层：年份 (Year)
            for year in os.listdir(family_path):
                year_path = os.path.join(family_path, year)
                if not os.path.isdir(year_path):
                    continue
                
                # --- 新增逻辑：处理特殊年份名称 ---
                display_year = year
                if display_year == "2020-2023":
                    display_year = "2023-before"
                    
                # 按照 "家族-年份.txt" 命名
                output_filename = f"{family}-{display_year}.txt"
                output_file_path = os.path.join(output_dir, output_filename)
                
                malicious_hashes = []
                
                # 遍历第三层：具体的样本文件，提取 Hash 存入列表
                for filename in os.listdir(year_path):
                    file_path = os.path.join(year_path, filename)
                    if os.path.isfile(file_path):
                        file_hash = get_sha256(file_path)
                        if file_hash:
                            malicious_hashes.append(file_hash)
                
                # 写入文件：顶部写入总数，随后写入 Hash
                with open(output_file_path, "w", encoding="utf-8") as out_f:
                    out_f.write(f"Total: {len(malicious_hashes)}\n")
                    for h in malicious_hashes:
                        out_f.write(f"{h}\n")
                        
                print(f"[+] 提取完成: [{family}] 家族 ({display_year}) - 共 {len(malicious_hashes)} 个样本 -> {output_filename}")
    else:
        print("[-] 未找到 malicious 目录，请检查路径。")

    print(f"\n[√] 所有 Hash 提取任务完成！请前往 {output_dir} 查看结果。")

if __name__ == "__main__":
    main()