import os
import re
import requests
import chromadb
from sentence_transformers import SentenceTransformer
import zipfile
from tqdm import tqdm  # 新增：進度條套件
import time

# --- 配置區 ---
BASE_URL = "https://api-gateway.netdb.csie.ncku.edu.tw"
API_KEY = ""
MODEL = "gpt-oss:120b"

# 初始化本地 Embedding
print("正在載入 Embedding 模型...")
embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
print("✓ 模型載入完成")

chroma_client = chromadb.PersistentClient(path="./japan_db")

def prepare_corpus(zip_path, extract_path):
    if not os.path.exists(extract_path):
        print(f"偵測到壓縮檔，正在解壓縮至 {extract_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print("解壓縮完成。")
    else:
        print("資料夾已存在，跳過解壓。")

def clean_content(text):
    """專門針對 Japan-guide 結構設計的深度清洗函數"""
    # 1. 移除特定的側欄推薦區塊
    text = re.sub(r'\[##.*?\]\(/link\.html\?.*?\)', '', text, flags=re.DOTALL)
    
    # 2. 移除導覽、贊助內容與重複性訊息
    noise_patterns = [
        r"Show All .*? Kyoto",
        r"Show All .*? Osaka",
        r"How to get from .*? to .*?",
        r"View itinerary",
        r"Sponsored Story",
        r"Travel News",
        r"Traveling with Kids",
        r"Read our guide",
        r"Read more"
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 3. 移除 HTML 標籤
    text = re.sub(r'<[^>]+>', '', text)

    # 4. 移除 Markdown 中的空連結圖示與無效連結
    text = re.sub(r'\[\]\(.*?\)', '', text)
    text = re.sub(r'\* \[\]', '', text)

    # 5. 處理連續空白與空行
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def index_data(md_folder):
    """建立索引 - 新增詳細進度追蹤"""
    CHUNK_SIZE = 300
    OVERLAP = 50
    
    # 檢查是否需要重建索引
    try:
        collection = chroma_client.get_collection("docs")
        existing_count = collection.count()
        print(f"發現已存在的索引（{existing_count} 個 chunks）")
        user_input = "n"
        if user_input != 'y':
            print("保持現有索引，結束程序。")
            return
        chroma_client.delete_collection("docs")
        print("✓ 已清空舊索引")
    except:
        print("未找到舊索引，將建立新索引")
    
    collection = chroma_client.get_or_create_collection("docs")
    
    # 統計文件數量
    all_files = [f for f in os.listdir(md_folder) if f.endswith(".md")]
    excluded_files = [f for f in all_files if any(x in f.lower() for x in ['privacy', 'terms', 'feedback', 'advertising'])]
    valid_files = [f for f in all_files if f not in excluded_files]
    
    print(f"\n📊 資料統計：")
    print(f"   總文件數: {len(all_files)}")
    print(f"   排除文件: {len(excluded_files)}")
    print(f"   待處理: {len(valid_files)}")
    print(f"\n開始建立索引...\n")
    
    total_chunks = 0
    failed_files = []
    
    # 使用 tqdm 顯示進度條
    for fn in tqdm(valid_files, desc="處理文件", unit="檔"):
        try:
            file_path = os.path.join(md_folder, fn)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            match = re.search(r'^---\s*(.*?)\s*---\s*(.*)', raw_text, re.DOTALL)
            if not match: 
                failed_files.append((fn, "無法解析 YAML header"))
                continue
            
            header_text, body_text = match.group(1), match.group(2).strip()
            
            # 清洗內容
            body_text = clean_content(body_text)
            
            # 檢查清洗後是否還有內容
            if len(body_text) < 50:
                failed_files.append((fn, "清洗後內容過少"))
                continue
            
            # 提取 Metadata
            metadata = {}
            for line in header_text.split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    metadata[k.strip()] = v.strip()

            clean_metadata = {
                "url": metadata.get("url", ""),
                "title": metadata.get("title", fn.replace('.md', '')),
                "description": metadata.get("description", ""),
                "keywords": metadata.get("keywords", ""),
                "content_type": metadata.get("content_type", "")
            }

            # 切割並建立索引
            start = 0
            i = 0
            while start < len(body_text):
                end = start + CHUNK_SIZE
                chunk = body_text[start:end]
                
                searchable_text = f"TITLE: {clean_metadata['title']}\nKEYWORDS: {clean_metadata['keywords']}\nINFO: {chunk}"
                
                collection.add(
                    ids=[f"{fn}_{i}"],
                    documents=[searchable_text],
                    embeddings=[embed_model.encode(searchable_text).tolist()],
                    metadatas=[clean_metadata]
                )
                
                total_chunks += 1
                start += (CHUNK_SIZE - OVERLAP)
                i += 1
                if len(body_text) - start < 50: break
        
        except Exception as e:
            failed_files.append((fn, str(e)))
    
    # 顯示結果
    print(f"\n{'='*60}")
    print(f"✓ 索引建立完成！")
    print(f"  - 成功處理: {len(valid_files) - len(failed_files)} 個文件")
    print(f"  - 總 Chunks: {total_chunks}")
    print(f"  - 資料庫大小: {collection.count()} 個向量")
    
    if failed_files:
        print(f"\n失敗文件 ({len(failed_files)}):")
        for fn, reason in failed_files[:5]:  # 只顯示前5個
            print(f"   - {fn}: {reason}")
        if len(failed_files) > 5:
            print(f"   ... 還有 {len(failed_files)-5} 個")
    print(f"{'='*60}\n")

def query_rag_with_filter(location, question):
    """改良版檢索函數"""
    collection = chroma_client.get_collection("docs")
    
    query_text = f"{location} {question}"
    query_emb = embed_model.encode(query_text).tolist()
    
    print(f"🔍 正在檢索關於「{location}」的資訊...")
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=5, 
        where_document={"$contains": location} 
    )

    if not results['documents'][0]:
        return f"❌ 找不到關於「{location}」的具體資訊。"

    context_list = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_list.append(f"【資料來源：{meta['title']}】\nURL: {meta['url']}\n內容: {doc}")
    
    return "\n---\n".join(context_list)

if __name__ == "__main__":
    print("=" * 60)
    print("日本旅遊 RAG 系統 - 索引建立工具")
    print("=" * 60 + "\n")
    
    zip_file = r"C:\計算理論\travel_agent\japan_deep_corpus.zip"
    data_path = r"C:\計算理論\travel_agent\japan_deep_corpus"
    
    # 步驟 1: 準備資料
    if os.path.exists(zip_file):
        prepare_corpus(zip_file, data_path)
    
    # 步驟 2: 建立索引
    start_time = time.time()
    index_data(data_path)
    elapsed = time.time() - start_time
    print(f"⏱️  總耗時: {elapsed:.2f} 秒")
    
    # 步驟 3: 測試檢索
    print("\n" + "="*60)
    print("測試檢索功能")
    print("="*60)
    loc = "Osaka"
    q = "大阪有哪些預算低的景點或省錢交通工具？"
    result = query_rag_with_filter(loc, q)
    print(len(result))
