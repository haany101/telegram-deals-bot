import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime

# ============================================================
#  إعدادات البوت
# ============================================================
BOT_TOKEN = "8798195240:AAEJeshx3j4bfKa9u0xygTI0u59oHJGNMWg"
CHAT_ID = "-1003898984007"
CHECK_INTERVAL = 1800  # كل 30 دقيقة

# ============================================================
#  كيبورد البحث
# ============================================================
SEARCH_KEYWORDS = [
    "laptop gaming", "gaming headset", "mechanical keyboard",
    "gaming mouse", "gaming monitor", "لابتوب", "سماعة gaming",
    "كيبورد gaming", "ماوس gaming", "شاشة gaming",
]

# ============================================================
#  عروض تم إرسالها (لتجنب التكرار)
# ============================================================
sent_deals = set()

# ============================================================
#  إرسال رسالة للقناة
# ============================================================
async def send_message(session: aiohttp.ClientSession, text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            if not result.get("ok"):
                print(f"[Send Error] {result}")
    except Exception as e:
        print(f"[Send Exception] {e}")

# ============================================================
#  سحب عروض أمازون RSS
# ============================================================
async def fetch_amazon_deals(session: aiohttp.ClientSession) -> list:
    deals = []
    feeds = [
        "https://www.amazon.sa/rss/bestsellers/electronics",
        "https://www.amazon.sa/rss/movers-and-shakers/electronics",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DealsBot/1.0)"}

    for feed_url in feeds:
        try:
            async with session.get(feed_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    root = ET.fromstring(text)
                    channel = root.find("channel")
                    if channel:
                        for item in channel.findall("item")[:15]:
                            title = item.findtext("title", "")
                            link = item.findtext("link", "")
                            desc = item.findtext("description", "")

                            if any(kw.lower() in title.lower() or kw.lower() in desc.lower()
                                   for kw in SEARCH_KEYWORDS):
                                deal_id = link.split("/dp/")[-1].split("/")[0] if "/dp/" in link else link[:50]
                                if deal_id not in sent_deals:
                                    deals.append({
                                        "title": title,
                                        "url": link,
                                        "source": "🇸🇦 Amazon SA",
                                        "deal_id": deal_id,
                                    })
        except Exception as e:
            print(f"[RSS Error] {e}")

    return deals

# ============================================================
#  تنسيق الرسالة
# ============================================================
def format_deal(deal: dict) -> str:
    msg = f"🔥 <b>{deal['title'][:200]}</b>\n\n"
    if deal.get("sale_price"):
        msg += f"💰 السعر: <b>{deal['sale_price']}</b>\n"
    if deal.get("original_price"):
        msg += f"~~{deal['original_price']}~~\n"
    if deal.get("discount"):
        msg += f"🏷️ خصم: <b>{deal['discount']}%</b>\n"
    msg += f"🛒 المتجر: {deal.get('source', '')}\n"
    msg += f"\n🔗 <a href='{deal['url']}'>اضغط للشراء</a>"
    return msg

# ============================================================
#  الحلقة الرئيسية
# ============================================================
async def main():
    print(f"✅ البوت شغال!")
    print(f"📡 القناة: {CHAT_ID}")

    async with aiohttp.ClientSession() as session:
        # رسالة ترحيب
        await send_message(session, "🤖 <b>بوت عروض الكمبيوتر شغال!</b>\n\nراح يرسل لك أحسن عروض الإلكترونيات كل 30 دقيقة 🔥")

        while True:
            print(f"\n[{datetime.now().strftime('%H:%M')}] جاري البحث عن عروض...")

            deals = await fetch_amazon_deals(session)

            if deals:
                for deal in deals[:5]:
                    msg = format_deal(deal)
                    await send_message(session, msg)
                    sent_deals.add(deal["deal_id"])
                    await asyncio.sleep(2)
                print(f"✅ تم إرسال {len(deals[:5])} عروض")
            else:
                print("😴 ما في عروض جديدة الحين")

            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
