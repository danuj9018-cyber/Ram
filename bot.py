from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import UserNotParticipantError
import asyncio
import re
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render Port Handler (Health Check)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is Running Successfully!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Web Server listening on port {port}")
    server.serve_forever()

# ---------- 🔐 CREDENTIALS ----------
API_ID = 32838397
API_HASH = "8d4f2f91eb844fa89939a7e1efcfee20"
BOT_TOKEN = "7970774532:AAFey27uvaRO4AR93caFfT3UPFzsXFyk0KU"
STRING_SESSION = "1BVtsOKUBuzrh0vbqvFdoV2XeVlh64ERa0tqmbF17HeLIP1s7H4FLuIxnIcsuVtlmnsVADO4_N4wCOJSOe5xR5bdiuqEdEsYhC0-FEPjgJic4eYUqEIPHAqOfeR9EYSGyKRbxWXPKqgmIE038PlhNSeN7mnCUygaTM02rvaxbtxr5_cKoMaKSYKbjWGWUoqziOScWfQYAvYTA-53T5c7YyPPaoahmDPVQ2rjkxV59tqwnMjOaXgaO1-TWnOPtnWcWkHO5j5C-bmbkOcbHGao2Zak7Xm4xUI09av_xs1_f3IW3AlJteKN9IJ8TmbQ94AVVuo3iPZtxY3ATFEAS2pu7AaxffNqBnac="

TARGET = "@Nick_Bypass_Bot"

# 📢 FORCE JOIN CONFIGURATION
MUST_JOIN_CHANNEL = -1003596848844
MUST_JOIN_LINK = "https://t.me/+0LRzgoMtRJBlMWY1"

user_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
bot_client = TelegramClient("bot_session", API_ID, API_HASH)

pending_requests = {}

async def is_user_joined(user_id):
    try:
        permissions = await bot_client.get_permissions(MUST_JOIN_CHANNEL, user_id)
        if permissions:
            return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"⚠️ Force Join Check Error: {e}")
        return True
    return False

async def send_must_join_msg(event):
    buttons = [
        [Button.url("🔗 Join Channel", MUST_JOIN_LINK)],
        [Button.inline("✅ I have joined", data=b"check_join")]
    ]
    msg_text = (
        "🤖 Welcome!\n\n"
        "To use this bot, you must join our channel first:\n\n"
        f"🔗 {MUST_JOIN_LINK}\n\n"
        "After joining, click '✅ I have joined' button below."
    )
    await event.reply(msg_text, buttons=buttons, link_preview=True)

@bot_client.on(events.CallbackQuery(data=b"check_join"))
async def check_join_callback(event):
    user_id = event.sender_id
    if await is_user_joined(user_id):
        await event.answer("✅ Thank you! You can now use the bot.", alert=True)
        await event.delete()
        await bot_client.send_message(
            user_id,
            "🤖 **I am your Official Link bypasser Bot!**\n\n"
            "Just send me any link (URL), I will process it and give you the bypassed link.\n\n"
            "❤️‍🩹 _Developed by @nexunx ✅",
            parse_mode='md'
        )
    else:
        await event.answer("❌ You haven't joined the channel yet! Please join first.", alert=True)

@bot_client.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def bot_receive_link(event):
    user_id = event.sender_id

    if not await is_user_joined(user_id):
        await send_must_join_msg(event)
        return

    link = event.text

    if "http" not in link:
        await event.reply("❌ Please send a valid URL (link).")
        return

    wait_msg = await event.reply(
        "⏳ _Please Wait, Your Link is Being Processed..._\n➤ @𝑵𝒆𝒙𝒖𝒏𝒙 𝑺𝒆𝒓𝒗𝒆𝒓 ❤️‍🩹",
        parse_mode='md'
    )

    try:
        msg = await user_client.send_message(TARGET, link)
        pending_requests[msg.id] = (user_id, wait_msg.id)
        print(f"✅ Link sent, User ID: {user_id}")
    except Exception as e:
        await bot_client.delete_messages(user_id, wait_msg.id)
        await event.reply(f"❌ Error while sending via UserBot: {e}")

@user_client.on(events.NewMessage(chats=TARGET))
async def userbot_nick_reply(event):
    if not event.reply_to_msg_id:
        return

    if event.reply_to_msg_id not in pending_requests:
        return

    original_user_id, wait_msg_id = pending_requests[event.reply_to_msg_id]
    text = event.text

    if "processing" in text.lower():
        print("📨 'Processing...' ignored.")
        return

    try:
        await bot_client.delete_messages(original_user_id, wait_msg_id)
    except Exception as e:
        print(f"⚠️ Waiting message delete failed: {e}")

    original_url = None
    bypassed_url = None

    orig_match = re.search(r'Original Link:\s*(https?://[^\s]+)', text, re.IGNORECASE)
    byp_match = re.search(r'Bypassed Link:\s*(https?://[^\s]+)', text, re.IGNORECASE)

    if not orig_match:
        orig_match = re.search(r'Original Link:\s*\[.*?\]\((https?://[^\s]+)\)', text)
    if not byp_match:
        byp_match = re.search(r'Bypassed Link:\s*\[.*?\]\((https?://[^\s]+)\)', text)

    if orig_match:
        original_url = orig_match.group(1).strip()
    if byp_match:
        bypassed_url = byp_match.group(1).strip()

    if not original_url or not bypassed_url:
        urls = re.findall(r'https?://[^\s]+', text)
        if len(urls) >= 2:
            if not original_url:
                original_url = urls[0]
            if not bypassed_url:
                bypassed_url = urls[1]

    if original_url:
        original_url = re.sub(r'\*\*$', '', original_url).strip()
    if bypassed_url:
        bypassed_url = re.sub(r'\*\*$', '', bypassed_url).strip()

    if original_url and bypassed_url:
        new_msg = (
            f"✦ 𝒀𝒐𝒖𝒓 𝑳𝒊𝒏𝒌 𝑰𝒔 𝑹𝒆𝒂𝒅𝒚💀 ✦\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n\n"
            f"◈ 𝑶𝒓𝒊𝒈𝒊𝒏𝒂𝒍 𝑳𝒊𝒏𝒌✅\n"
            f"➤ [{original_url}]({original_url})\n\n\n"
            f"──────────────────\n\n\n"
            f"◈ 𝑩𝒚𝒑𝒂𝒔𝒔𝒆𝒅 𝑳𝒊𝒏𝒌✅\n"
            f"➤ [{bypassed_url}]({bypassed_url})\n\n"
            f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n\n"
            f"╰┈➤ ❝ Developed ❤️‍🔥by @nexunx ❝ "
        )
    else:
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if 'Powered By' in line or 'Time Taken' in line:
                continue
            if not line.strip():
                continue
            cleaned_lines.append(line)
        clean_text = '\n'.join(cleaned_lines)
        new_msg = f"{clean_text}\n\n╰┈➤ ❝ Developed❤️‍🔥 by @nexunx ❞"

    pending_requests.pop(event.reply_to_msg_id, None)
    await bot_client.send_message(original_user_id, new_msg, parse_mode='md')
    print(f"📨 Stylish result sent to User {original_user_id}")

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    user_id = event.sender_id

    if not await is_user_joined(user_id):
        await send_must_join_msg(event)
        return

    await event.reply(
        "🤖 **I am your Official Link bypasser Bot!**\n\n"
        "Just send me any link (URL), I will process it and give you the bypassed link.\n\n"
        "❤️‍🩹 _Developed by @nexunx ✅",
        parse_mode='md'
    )

async def main():
    # Start web server first to bind PORT immediately for Render
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ Bot & UserBot Started!")

    # Keep both clients running
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
                       
