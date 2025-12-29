# services/chat_service.py

from llm.client import call_llm


def chat_with_ai(user_message: str, chat_history: list = None) -> str:
    """
    AI 旅遊顧問對話功能
    
    參數:
        user_message: 使用者的問題
        chat_history: 對話歷史 (可選)
    
    返回:
        AI 的回應
    """
    
    # 建立對話上下文
    context = ""
    if chat_history and len(chat_history) > 0:
        # 只保留最近 5 輪對話作為上下文
        recent_history = chat_history[-10:]  # 最近 5 輪 = 10 條訊息（用戶+AI）
        for msg in recent_history:
            role = "使用者" if msg["role"] == "user" else "AI助手"
            context += f"{role}: {msg['content']}\n"
    
    # 組合完整 prompt
    system_prompt = """你是一位專業且友善的日本旅遊顧問助手。

你的職責：
1. 回答關於日本旅遊的各種問題
2. 提供實用的旅遊建議和資訊
3. 解答簽證、交通、住宿、美食等相關疑問
4. 用親切、專業的語氣與使用者互動

回答原則：
- 保持簡潔明瞭，避免過長的回答
- 提供具體實用的建議
- 如果不確定，誠實告知並建議查詢官方資訊
- 適時提供相關的延伸資訊
- 用友善的語氣，讓使用者感到被重視

請用繁體中文回答。
"""

    # 如果有對話歷史，加入上下文
    if context:
        full_prompt = f"""{system_prompt}

以下是之前的對話記錄：
{context}

使用者的新問題：{user_message}

請根據對話歷史和新問題，給出適當的回應："""
    else:
        full_prompt = f"""{system_prompt}

使用者問題：{user_message}

請回答："""
    
    # 呼叫 LLM
    response = call_llm(full_prompt)
    
    return response


def get_quick_answer(question_type: str) -> str:
    """
    快速回答常見問題
    
    參數:
        question_type: 問題類型 (visa, currency, wifi, luggage)
    
    返回:
        預設的回答內容
    """
    
    quick_answers = {
        "visa": """📝 **台灣人赴日簽證資訊**

✅ **好消息！台灣護照免簽證**
- 停留期限：90 天以內
- 需要文件：有效護照、回程機票
- 入境前建議：完成 Visit Japan Web 登記

⚠️ **注意事項**
- 護照效期需超過停留天數
- 不可從事有報酬工作
- 建議準備住宿證明

有其他簽證相關問題嗎？歡迎繼續提問！""",

        "currency": """💱 **日本換匯建議**

💡 **最划算的換匯方式**
1. **在台灣換**：通常匯率較好，建議在銀行或機場換一部分
2. **日本 ATM**：可用金融卡提領日圓，手續費較低
3. **信用卡**：大部分商店接受，減少現金需求

🏦 **建議額度**
- 5天行程：¥30,000 - ¥50,000 現金
- 其餘使用信用卡

❌ **避免**
- 日本機場換匯（匯率較差）
- 在台灣機場換太多（不便攜帶）

需要更詳細的換匯建議嗎？""",

        "wifi": """📱 **日本上網方案比較**

🌐 **三種主要選擇**

1. **SIM 卡** 👍 推薦
   - 優點：方便、網速快、不用還
   - 缺點：需換卡、無法分享
   - 適合：單人旅行、手機有雙卡

2. **WiFi 分享器**
   - 優點：多人共用、網速穩定
   - 缺點：需充電、要歸還
   - 適合：2人以上、長時間使用

3. **eSIM**
   - 優點：最方便、不用換卡
   - 缺點：手機需支援、價格較高
   - 適合：支援 eSIM 的手機用戶

💡 **使用建議**
- 短期旅遊（3-5天）：eSIM 或 SIM 卡
- 長期或多人：WiFi 分享器
- 預算有限：SIM 卡

需要推薦特定品牌嗎？""",

        "luggage": """🎒 **日本旅遊行李清單**

📋 **必備文件**
- ✅ 護照（效期6個月以上）
- ✅ 機票（電子機票可）
- ✅ 住宿確認單
- ✅ 旅遊保險單
- ✅ Visit Japan Web（QR Code）

👔 **衣物建議**（視季節調整）
- 換洗衣物（建議輕便、易乾）
- 輕薄外套（室內冷氣強）
- 舒適步行鞋
- 雨具（折疊傘）

💊 **藥品與用品**
- 個人常用藥
- OK繃、感冒藥
- 防曬用品
- 保養品、化妝品

🔌 **3C 用品**
- 手機、充電器
- 行動電源
- 轉接插頭（日本A型）
- 相機（可選）

💡 **小提醒**
- 日本便利商店很方便，忘記帶可以買
- 避免攜帶過多液體（託運限制）
- 留些空間給戰利品

還想知道特定季節的建議嗎？"""
    }
    
    return quick_answers.get(question_type, "抱歉，找不到相關資訊。請直接提問！")