# services/search_service.py

import re
import online
from llm.client import call_llm
from fsm.state import FSMResult
from rag import query_rag_with_filter
import time
import tiktoken
def count_tokens(text):
    # 使用 cl100k_base 編碼（適用於 GPT-4 等，估算 Llama/Qwen 也很好用）
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)

def llm_search(
    location: str,
    days: int,
    budget: int,
    query: str,
    people: int,
    fsm_result: FSMResult,
    start_date: str = None,
    end_date: str = None,
    accommodation: str = None,
    interests: list = None
) -> str:
    """
    依 FSM State + 使用者輸入組 prompt，並整合工具調用功能
    """
    
    budget_text = (
        f"預算約 {budget:,} 元台幣（每人）"
        if fsm_result.state == "A" and budget
        else "使用者未提供明確預算，請提供彈性方案"
    )

    # 處理額外需求
    extra_req = query if query and query.strip() else "無特別需求"

    # 日期資訊（如果有的話）
    date_info = ""
    if start_date and end_date:
        date_info = f"\n- 出發日期：{start_date}\n- 回程日期：{end_date}"

    # 住宿偏好（如果有的話）
    accommodation_info = ""
    if accommodation:
        accommodation_info = f"\n- 住宿偏好：{accommodation}"

    # 興趣標籤（如果有的話）
    interests_info = ""
    if interests and len(interests) > 0:
        interests_info = f"\n- 興趣愛好：{', '.join(interests)}"

    # ========== 第一次 LLM：生成帶標記的回答 + RAG 檢索問題 ==========
    first_prompt = f"""你是一位日本旅遊資訊助理。
    【絕對指令】：
1. 無論參考資料是什麼語言，你必須「全程使用繁體中文」回答。
2. 只有景點名稱、店名可以保留日文括號備註（例如：清水寺 (Kiyomizu-dera)），其餘敘述嚴禁使用日文或英文。
回答以下旅遊規劃需求，但在需要查詢實際資料的地方使用特殊標記
可用函數標記格式：
- [CALL:search_places:關鍵字] - 搜尋地點
多使用這個標記來取得最新資訊，並在回答中插入地點名稱列表。
使用者的旅遊條件如下：
- 目的地：{location}
- 停留天數：{days} 天
- 旅遊人數：{people} 人
- 預算：{budget_text}{date_info}{accommodation_info}{interests_info}
- 旅遊偏好與需求：{extra_req}

請根據以上資訊，提供實用的旅遊建議，包含：

1. **行程規劃**：逐日安排（Day 1 到 Day {days}），包含具體景點和時間安排 
2. **住宿建議**：根據預算和偏好推薦適合的住宿區域和類型
3. **交通指南**：機場往返、市區交通方式和交通卡建議
4. **美食推薦**：必吃料理和餐廳推薦
5. **景點介紹**：主要景點特色和遊覽時間
6. **預算分配**：大致的花費估算（機票、住宿、餐飲、交通、門票等）
等等會根據這裡的資訊以及函式產生的結果來回答，所以為了讓prompt length不要太大，請不要到太詳細，簡短扼要著重在哪裡需要函數呼叫來取得實際數據。
請用友善、專業的語氣回答，讓使用者感受到貼心的服務。
特別注意要根據使用者的興趣和偏好來客製化建議。

請依照以上資訊，給出以下旅遊建議，並在需要實際數據的地方插入標記：
[機票] [住宿] [景點] [美食] [行程規劃]

重要提示：
1. 使用 [CALL:search_places:關鍵字] 搜尋特定類型的地點（如：大阪機場附近的飯店）
2. 不要在標記中直接使用座標，只使用地點名稱

例如：
推薦住宿：[CALL:search_places:大阪市區飯店]

 **最後一定要生成一個 RAG 檢索問題**，格式為：
[RAG_QUERY:你的檢索問題]

RAG 檢索問題應該是一個簡潔的問句，用來從旅遊知識庫中檢索相關資訊。例如：
- [RAG_QUERY:東京有哪些適合室內活動的景點？]
- [RAG_QUERY:大阪美食推薦有哪些？]
- [RAG_QUERY:京都賞楓季節的住宿建議]

現在請回答："""

    print("\n【第一次 LLM 呼叫】生成帶標記的回答...\n")
    first_response = call_llm(first_prompt)
    
    if not first_response:
        return "查詢失敗，請稍後再試"
    
    print(f"原始回答:\n{first_response}\n")
    print(f"{'='*60}\n")
    
    # ========== 提取 RAG 檢索問題 ==========
    rag_query = None
    rag_pattern = r'\[RAG_QUERY:(.*?)\]'
    rag_match = re.search(rag_pattern, first_response)
    
    if rag_match:
        rag_query = rag_match.group(1).strip()
        print(f"【RAG 檢索】提取到檢索問題: {rag_query}\n")
        # 移除 RAG_QUERY 標記，避免出現在最終回答中
        first_response = re.sub(rag_pattern, '', first_response).strip()
    else:
        print("【RAG 檢索】未檢測到 RAG_QUERY 標記，使用預設問題\n")
        rag_query = f"{location}的旅遊景點和美食推薦"
    
    # ========== 執行 RAG 檢索 ==========
    print(f"正在檢索: {rag_query}...\n")
    context = query_rag_with_filter(location, rag_query)
    print(f"RAG 檢索完成\n")
    print(f"{'='*60}\n")
    
    # ========== 解析並執行工具呼叫 ==========
    print("【工具執行階段】解析標記並執行工具...\n")
    
    # 找出所有標記
    pattern = r'\[CALL:(.*?)\]'
    matches = re.findall(pattern, first_response)
    
    if not matches:
        print( "未檢測到工具呼叫標記\n")
    else:
        print(f"檢測到 {len(matches)} 個工具呼叫\n")
    
    # 逐一處理標記
    processed_response = first_response
    tool_results_summary = []
    
    for idx, match in enumerate(matches, 1):
            parts = match.split(':', 1)  
            if len(parts) < 2: continue
            
            func_type, params = parts[0], parts[1].strip()
            
            try:
                if func_type == "search_places":
                    print(f"{idx}. 🔧 搜尋: {params}")
                    result = online.search_places_python(params, result_count=3)
                    
                    if result and len(result) > 0:
                        detailed_places = []
                        names_only = []
                        for p in result[:3]: # 每個標記取前 3 個最準確的地點
                            # 處理 Google API 新格式 (displayName.text) 或舊格式 (name)
                            name = p.get('displayName', {}).get('text', p.get('name', '未知地點'))
                            names_only.append(name)
                            
                            # 提取你要求的所有欄位
                            addr = p.get('address', '無地址資訊')           # 改用 'address'
                            rating = p.get('rating', '尚無評分')
                            user_count = p.get('user_ratings_total', 0)     # 改用 'user_ratings_total'
                            website = p.get('website', '無官方網站')         # 改用 'website'
                            phone = p.get('phone', '無聯繫電話')            # 改用 'phone'    
                            map_uri = p.get('google_maps_link', '#')        # 改用 'google_maps_link'
                            summary = p.get('summary', '無簡介')
                            
                            # 組裝詳細 Markdown 資訊
                            info_block = (
                                f"- **{name}**\n"
                                f"  * 評分：{rating} ({user_count} 則評論) \n"
                                f"  * 簡介：{summary}\n"
                                f"  * 地址：{addr}\n"
                                f"  * 電話：{phone}\n"
                                f"  * 官方網站：{website}\n"
                                f"  * Google Maps：{map_uri}"
                            )
                            detailed_places.append(info_block)
                        
                        # 替換草稿內容（保持草稿流暢，僅放入名字）
                        replacement = ", ".join(names_only)
                        processed_response = processed_response.replace(f"[CALL:{match}]", replacement, 1)
                        
                        # 將這 3 個地點的「完整數據」存入摘要，供第二次 LLM 參考
                        summary_entry = f"【搜尋「{params}」的精確數據】：\n" + "\n".join(detailed_places)
                        tool_results_summary.append(summary_entry)
                    else:
                        processed_response = processed_response.replace(f"[CALL:{match}]", "暫無搜尋結果", 1)

            except Exception as e:
                print(f"   執行錯誤: {e}")

    print(f"{'='*60}\n【第二次 LLM 呼叫】整合所有數據生成最終答案...\n")
    
    final_prompt = f"""你是一位專業的日本旅遊規劃師。請根據以下資訊，生成一份精美、詳實且專業的旅遊建議。

【重要格式要求】：
1. **隱藏技術過程**：嚴禁在回答中提及「根據 RAG 檢索」、「工具查詢結果顯示」、「模型思考」或任何關於資料獲取過程的文字。請直接以專業顧問的口吻給出建議。
2. **行程表格化**：請務必將「1. 行程規劃」的部分整理成一個清晰的 **Markdown 表格**，欄位必須包含：天數/時間、景點/活動名稱、內容詳述、交通方式。
3. **天數過長，簡化表格** :停留若超過五天，把所有行程合成一個大表格，縱軸是時間，橫軸是天數，內容是景點/活動名稱與交通方式。
使用者的旅遊條件如下：
- 目的地：{location}
- 停留天數：{days} 天
- 旅遊人數：{people} 人
- 預算：{budget_text}{date_info}{accommodation_info}{interests_info} (找出最接近預算的行程)
- 旅遊偏好與需求：{extra_req}

請整合以下數據生成最終回答：
- 知識庫參考：{context}
- 即時工具數據（請優先引用此處的具體景點與餐廳名）：{chr(10).join(tool_results_summary) if tool_results_summary else '無工具查詢結果'}
- 原始草稿參考：{processed_response}

回答應包含：
1. **行程規劃**（請以表格呈現）
2. **住宿建議**（推薦具體區域與 Google 推薦的飯店）
3. **交通指南**（包含 N'EX、Suica 等實用資訊）
4. **美食與景點詳細介紹**（引用工具查詢到的具體數據，如評分與特色）
5. **預算分配估算**（以條列式呈現）

請生成最終回答："""
    print("final_prompt token length:", count_tokens(final_prompt))
    final_response = call_llm(final_prompt)
    print(f"最終回答:\n{final_response}\n")
    return final_response