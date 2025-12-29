import requests
import json

API_KEY = "AIzaSyBbMkKmWfqt4BzXVMHobt_kMKmeNdeY6lY"

def search_places_python(query):
    url = "https://places.googleapis.com/v1/places:searchText"
    
    # 1. 在 FieldMask 增加更多欄位
    # 常用欄位參考：websiteUri, internationalPhoneNumber, regularOpeningHours, priceLevel, types, googleMapsUri
    fields = [
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.userRatingCount",
        "places.websiteUri",                # 官方網站
        "places.internationalPhoneNumber",   # 國際格式電話
        "places.priceLevel",                # 價位 (例如 PRICE_LEVEL_MODERATE)
        "places.googleMapsUri",             # 直接打開 Google Map 的連結
        "places.editorialSummary"           # 餐廳/景點的簡短介紹
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": ",".join(fields)
    }
    
    data = {
        "textQuery": query,
        "languageCode": "zh-TW",
        "regionCode": "JP",  # 強制指定日本地區
        "maxResultCount": 3
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        results = response.json().get('places', [])
        places_info = []    
        
        for place in results:
            # 2. 解析新增的欄位
            name = place.get('displayName', {}).get('text', '無名稱')
            address = place.get('formattedAddress', '無地址')
            rating = place.get('rating', '尚無評分')
            user_ratings = place.get('userRatingCount', 0)
            
            # 取得簡介 (有些地點可能沒有)
            summary = place.get('editorialSummary', {}).get('text', '尚無簡介')
            

            places_info.append({
                'name': name,
                'address': address,
                'rating': rating,
                'user_ratings_total': user_ratings,
                'phone': place.get('internationalPhoneNumber', '無電話'),
                'website': place.get('websiteUri', '無網站'),
                'google_maps_link': place.get('googleMapsUri', ''),
                'summary': summary,
                'price_level': place.get('priceLevel', '未知價位')
            })
        
        return places_info
    else:
        print(f"Error: {response.status_code}")
        return []

# 測試與印出結果
# results = search_places_python("大阪機場附近的飯店")

# for i, p in enumerate(results, 1):
#     print(f"\n{i}. {p['name']} 【{p['status']}】")
#     print(f"   ⭐ 評分：{p['rating']} ({p['user_ratings_total']} 則評論)")
#     print(f"   📝 簡介：{p['summary']}")
#     print(f"   📞 電話：{p['phone']}")
#     print(f"   🔗 網址：{p['website']}")
#     print(f"   📍 地圖：{p['google_maps_link']}")

