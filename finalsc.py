"""
=============================================================================
🎫 SCRATCH THE WIN - OFFICIAL TELEGRAM MINI APP BOT (ZERO-DEPENDENCY ENGINE) 🎫
=============================================================================
100% Pure Python Standard Library Telegram Bot Engine.
✅ NO 'pip install' required! Works directly in VS Code, uv Python 3.14, CMD, Render & VPS!
✅ Zero ModuleNotFoundError - uses built-in urllib & json to talk directly to Telegram API.

Flow:
1. User sends /start -> Mandatory Channel Join (2x4 Grid '✔ Join' buttons + '✔ Claim')
2. User joins channels & clicks '✔ Claim' -> Real-time Channel Verification
3. Once channels verified -> Step 2: Strict Device Verification
4. Strict device verification in WebApp -> Home unlock + Instant payment notification
5. Every new user gets strictly 1 Scratch Card.
6. Per referral: +1 Free Scratch Card awarded after friend's 1st scratch in Firebase RTDB.
7. Admin Commands: /ownerhelp, /channels, /addchannel, /removechannel, /emojitest, /broadcast, /stats.
=============================================================================
"""

import os
import sys
import json
import time
import re
import threading
import logging
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# 1. CORE BOT CONFIGURATION
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN", "8611638952:AAEYJAhc5_s7RqYFunD6UofwqrgR3McnYu8").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "scratch_the_upi_bot").strip().lstrip("@")
WEB_URL = os.environ.get("WEB_URL", "https://scbotxyz.vercel.app/").strip().rstrip("/")
RTDB_URL = os.environ.get("RTDB_URL", "https://scratch-7d728-default-rtdb.firebaseio.com").strip().rstrip("/")
TG_API_BASE = f"https://api.telegram.org/bot{TOKEN}"

# ---------------------------------------------------------------------------
# 2. DEFAULT MANDATORY CHANNELS (2 COLUMNS x 4 ROWS)
# ---------------------------------------------------------------------------
PERMANENT_CHANNELS = [
    {
        "id": "-1003479783999",
        "name": "Official Channel 1",
        "url": "https://t.me/+7clQNCkYuAAxYWQ1",
        "is_private": True,
    },
    
]

# ---------------------------------------------------------------------------
# 3. AUTHORIZED BOT OWNERS
# ---------------------------------------------------------------------------
DEFAULT_OWNERS = [
    "rohit79041",
    "Lokesh957232",
]

# ---------------------------------------------------------------------------
# 4. LOGGING CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("scratch_the_win_bot")


# ---------------------------------------------------------------------------
# 5. RENDER / VPS 24/7 HTTP HEALTH SERVER
# ---------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        res = {
            "status": "online",
            "bot": "Scratch The Win Telegram Bot",
            "web_url": WEB_URL,
            "uptime": int(time.time()),
        }
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health server note: {e}")


# ---------------------------------------------------------------------------
# 6. TELEGRAM BOT API CLIENT (PURE PYTHON - NO EXTERNAL PACKAGES)
# ---------------------------------------------------------------------------
_BOT_INFO_CACHE = None


def tg_api(method: str, payload: dict = None, timeout: int = 35) -> dict:
    url = f"{TG_API_BASE}/{method}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            return json.loads(err_body)
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def get_bot_info() -> dict:
    global _BOT_INFO_CACHE
    if _BOT_INFO_CACHE:
        return _BOT_INFO_CACHE
    res = tg_api("getMe", {})
    if res.get("ok") and res.get("result"):
        _BOT_INFO_CACHE = res["result"]
        return _BOT_INFO_CACHE
    return {"id": 0, "username": BOT_USERNAME}


def send_message(chat_id, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("sendMessage", payload)


def edit_message_text(chat_id, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("editMessageText", payload)


def answer_callback_query(callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    return tg_api("answerCallbackQuery", payload)


def forward_message(chat_id, from_chat_id, message_id: int) -> dict:
    return tg_api(
        "forwardMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        },
    )


def copy_message(chat_id, from_chat_id, message_id: int) -> dict:
    return tg_api(
        "copyMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        },
    )


def has_custom_emoji(message: dict) -> bool:
    if not message:
        return False
    entities = message.get("entities") or message.get("caption_entities") or []
    return any(e.get("type") == "custom_emoji" for e in entities)


def deliver_premium_message(target_chat_id, source_chat_id, message: dict) -> dict:
    """
    Guarantees 100% delivery of Telegram Premium animated custom emojis:
    1. If the message has custom_emoji entities, 'forwardMessage' preserves the sender's
       Telegram Premium custom_emoji rendering on all Telegram clients even if the bot
       itself does not have a paid Fragment username.
    2. Also supports direct entity preservation (entities / caption_entities) and falls
       back to copyMessage if needed.
    """
    msg_id = message.get("message_id")
    if has_custom_emoji(message):
        res = forward_message(target_chat_id, source_chat_id, msg_id)
        if res.get("ok"):
            return res

        # Fallback: explicitly pass entities / caption_entities without parse_mode
        entities = message.get("entities")
        caption_entities = message.get("caption_entities")
        reply_markup = message.get("reply_markup")

        if message.get("text") and entities:
            payload = {
                "chat_id": target_chat_id,
                "text": message["text"],
                "entities": entities,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            res2 = tg_api("sendMessage", payload)
            if res2.get("ok"):
                return res2

        if caption_entities:
            copy_payload = {
                "chat_id": target_chat_id,
                "from_chat_id": source_chat_id,
                "message_id": msg_id,
                "caption": message.get("caption", ""),
                "caption_entities": caption_entities,
            }
            if reply_markup:
                copy_payload["reply_markup"] = reply_markup
            res3 = tg_api("copyMessage", copy_payload)
            if res3.get("ok"):
                return res3

    return copy_message(target_chat_id, source_chat_id, msg_id)


# ---------------------------------------------------------------------------
# 7. DATABASE HELPER FUNCTIONS (FIREBASE RTDB REST)
# ---------------------------------------------------------------------------
def db_request(endpoint: str, method: str = "GET", data: any = None) -> any:
    url = f"{RTDB_URL}/{endpoint.lstrip('/')}"
    try:
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8")
            if content and content != "null":
                return json.loads(content)
            return None
    except Exception as e:
        logger.debug(f"DB request note [{method} {endpoint}]: {e}")
        return None


def get_user_from_db(user_id: str) -> dict | None:
    return db_request(f"users/{user_id}.json")


def is_already_referred(referrer_id: str, new_user_id: str) -> bool:
    res = db_request(f"referrals/{referrer_id}/{new_user_id}.json")
    return res is not None


def record_referral(referrer_id: str, new_user_id: str, name: str, username: str, status: str = "pending_first_scratch"):
    payload = {
        "joinerId": str(new_user_id),
        "name": name or f"User #{new_user_id}",
        "username": username or "",
        "status": status,
        "timestamp": int(time.time() * 1000),
    }
    db_request(f"referrals/{referrer_id}/{new_user_id}.json", method="PUT", data=payload)


def record_channel_joined(user_id: str, channel_id: str):
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    db_request(f"channel_joins/{user_id}/{clean_ch}.json", method="PUT", data=True)


def remove_channel_joined(user_id: str, channel_id: str):
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    db_request(f"channel_joins/{user_id}/{clean_ch}.json", method="DELETE")


def is_channel_joined_in_db(user_id: str, channel_id: str) -> bool:
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    res = db_request(f"channel_joins/{user_id}/{clean_ch}.json")
    return res is True


# ---------------------------------------------------------------------------
# 8. CHANNELS, OWNERS & TELEGRAM PREMIUM ANIMATED EMOJI ENGINE
# ---------------------------------------------------------------------------
_CHANNELS_CACHE = []
_OWNERS_CACHE = set(o.lower().lstrip("@") for o in DEFAULT_OWNERS)
_LAST_CACHE_TIME = 0

# Verified Telegram Custom Emoji IDs (Auto-enriched at startup via Telegram API + Firebase RTDB)
_PREMIUM_EMOJI_MAP = {
    "✔": "5206607081334906820",
    "✅": "5206607081334906820",
    "🔥": "5312241539987020022",
    "👑": "5312322066328853156",
    "🎉": "5312486361243062266",
    "🎁": "5312315739842026355",
    "🛫": "5312409003186199286",
    "🚨": "5312526098985124879",
    "🌺": "5312138559556164615",
    "😍": "5312513303690351633",
    "🍑": "5312383351024260855",
    "👥": "5312424912994963580",
    "🚀": "5312409003186199286",
    "⚠️": "5312526098985124879",
    "🔄": "5312189624351726761",
    "👌": "5368324170671202286",
    "🔗": "5312361223344363506",
    "📊": "5312279665405073798",
    "🚫": "5312157676413655955",
}


def pe(char: str) -> str:
    """
    Wraps a normal emoji in Telegram Premium <tg-emoji emoji-id="...">char</tg-emoji> tag.
    """
    eid = _PREMIUM_EMOJI_MAP.get(char)
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'
    return char


def pbtn(text: str, emoji_char: str = None, **kwargs) -> dict:
    """
    Creates an InlineKeyboardButton with Telegram Premium icon_custom_emoji_id
    (Bot API 9.4+) alongside standard fallback.
    """
    btn = {"text": text}
    btn.update(kwargs)
    if emoji_char and _PREMIUM_EMOJI_MAP.get(emoji_char):
        btn["icon_custom_emoji_id"] = str(_PREMIUM_EMOJI_MAP[emoji_char])
    return btn


def init_premium_emojis():
    """
    Fetches official live animated custom_emoji_id stickers directly from Telegram's servers
    (getForumTopicIconStickers) and merges any owner-saved custom emoji IDs from Firebase RTDB.
    """
    global _PREMIUM_EMOJI_MAP
    try:
        res = tg_api("getForumTopicIconStickers", {})
        if res.get("ok") and isinstance(res.get("result"), list):
            stickers = res["result"]
            by_emoji = {}
            all_ids = []
            for st in stickers:
                cid = str(st.get("custom_emoji_id", "")).strip()
                em = st.get("emoji", "")
                if cid:
                    all_ids.append(cid)
                    if em and em not in by_emoji:
                        by_emoji[em] = cid

            # Map exact matching base emojis from Telegram official animated topic icons
            for k in list(_PREMIUM_EMOJI_MAP.keys()):
                if k in by_emoji:
                    _PREMIUM_EMOJI_MAP[k] = by_emoji[k]

            # Also map related semantic emojis from official stickers if available
            alias_pairs = [
                ("👑", ["👑", "🏆", "⭐", "💎"]),
                ("🔥", ["🔥", "⚡", "💥"]),
                ("🎉", ["🎉", "🥳", "🎊", "✨"]),
                ("🎁", ["🎁", "💎", "🏆", "💰"]),
                ("🛫", ["🛫", "✈️", "🚀", "⚡"]),
                ("🚨", ["🚨", "🔔", "❗", "⚠️", "🔥"]),
                ("🌺", ["🌺", "🌸", "🌷", "🌹", "🌻", "🍀"]),
                ("😍", ["😍", "❤️", "💖", "🥰", "🤩"]),
                ("🍑", ["🍑", "🍓", "🍒", "🍎", "🔥"]),
                ("👥", ["👥", "👤", "💬", "📢"]),
                ("🚀", ["🚀", "⚡", "🔥"]),
                ("⚠️", ["⚠️", "❗", "❓", "🔔"]),
                ("🔄", ["🔄", "⚡", "⏳"]),
                ("👌", ["👌", "👍", "✅"]),
                ("🔗", ["🔗", "📌", "📎"]),
                ("📊", ["📊", "📈", "💼"]),
                ("🚫", ["🚫", "❌", "⛔"]),
            ]
            for target_em, candidates in alias_pairs:
                for cand in candidates:
                    if cand in by_emoji:
                        _PREMIUM_EMOJI_MAP[target_em] = by_emoji[cand]
                        break
    except Exception as e:
        logger.debug(f"init_premium_emojis topic stickers note: {e}")

    # Load any custom emoji overrides saved by owner via /setemojis in Firebase RTDB
    try:
        saved = db_request("bot_config/premium_emojis.json")
        if isinstance(saved, dict):
            for k, v in saved.items():
                if v:
                    _PREMIUM_EMOJI_MAP[k] = str(v).strip()
    except Exception as e:
        logger.debug(f"init_premium_emojis rtdb note: {e}")


def send_message_smart(chat_id, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    """
    Sends a message with Premium <tg-emoji> tags and button icon_custom_emoji_id.
    Automatically falls back cleanly if any button icon_custom_emoji_id is rejected.
    """
    res = send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if not res.get("ok") and reply_markup:
        # Strip icon_custom_emoji_id from buttons if needed and retry while keeping <tg-emoji> in text
        clean_rows = []
        for row in reply_markup.get("inline_keyboard", []):
            clean_row = []
            for b in row:
                cb = dict(b)
                cb.pop("icon_custom_emoji_id", None)
                clean_row.append(cb)
            clean_rows.append(clean_row)
        res = send_message(chat_id, text, reply_markup={"inline_keyboard": clean_rows}, parse_mode=parse_mode)
    if not res.get("ok"):
        # Final safety fallback stripping <tg-emoji> wrapper tags so message never fails
        plain_html = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text)
        res = send_message(chat_id, plain_html, reply_markup=reply_markup, parse_mode=parse_mode)
    return res


def edit_message_text_smart(chat_id, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    res = edit_message_text(chat_id, message_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if not res.get("ok") and reply_markup:
        clean_rows = []
        for row in reply_markup.get("inline_keyboard", []):
            clean_row = []
            for b in row:
                cb = dict(b)
                cb.pop("icon_custom_emoji_id", None)
                clean_row.append(cb)
            clean_rows.append(clean_row)
        res = edit_message_text(chat_id, message_id, text, reply_markup={"inline_keyboard": clean_rows}, parse_mode=parse_mode)
    if not res.get("ok"):
        plain_html = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text)
        res = edit_message_text(chat_id, message_id, plain_html, reply_markup=reply_markup, parse_mode=parse_mode)
    return res


def load_channels() -> list[dict]:
    global _CHANNELS_CACHE, _LAST_CACHE_TIME
    now = time.time()
    if _CHANNELS_CACHE and (now - _LAST_CACHE_TIME < 10):
        return _CHANNELS_CACHE

    combined = [dict(p) for p in PERMANENT_CHANNELS]
    try:
        remote = db_request("bot_config/channels.json")
        if remote:
            items = list(remote.values()) if isinstance(remote, dict) else remote
            for item in items:
                if isinstance(item, dict) and item.get("id"):
                    if not any(str(c.get("id")) == str(item["id"]) for c in combined):
                        combined.append(item)
    except Exception as e:
        logger.warning(f"Error loading channels: {e}")

    _CHANNELS_CACHE = combined
    _LAST_CACHE_TIME = now
    return _CHANNELS_CACHE


def is_owner(user: dict) -> bool:
    if not user:
        return False
    uid = str(user.get("id", "")).lower()
    uname = str(user.get("username", "")).lower().lstrip("@")
    return uid in _OWNERS_CACHE or uname in _OWNERS_CACHE


def build_channels_keyboard(channels: list[dict], ref_param: str = None) -> dict:
    buttons = []
    for i in range(0, len(channels), 2):
        row = [pbtn("Join 🛫", emoji_char="🛫", url=channels[i]["url"])]
        if i + 1 < len(channels):
            row.append(pbtn("Join 🛫", emoji_char="🛫", url=channels[i + 1]["url"]))
        buttons.append(row)

    claim_callback = f"claim_{ref_param or 'none'}"
    buttons.append([pbtn("✔ Claim", emoji_char="✅", callback_data=claim_callback)])
    return {"inline_keyboard": buttons}


def check_user_channels(user_id: int) -> tuple[bool, list[dict]]:
    channels = load_channels()
    if not channels:
        return (True, [])

    unjoined = []
    for ch in channels:
        ch_id = str(ch.get("id", "")).strip()
        target = int(ch_id) if ch_id.lstrip("-").isdigit() else ch_id

        # 1. Always check live Telegram membership status first (detects if user left or was kicked!)
        res = tg_api("getChatMember", {"chat_id": target, "user_id": user_id})

        if res.get("ok") and res.get("result"):
            status = res["result"].get("status", "")
            if status in ["member", "administrator", "creator", "restricted"]:
                record_channel_joined(str(user_id), ch_id)
                continue
            elif status in ["left", "kicked"]:
                # If user sent a join request to a private channel (not auto-approved yet),
                # Telegram status is still "left", so allow if join request was recorded in DB.
                # However, if user had joined and later left, chat_member update removes it from DB!
                if is_channel_joined_in_db(str(user_id), ch_id):
                    continue
                unjoined.append(ch)
                continue
        else:
            # If user is not a member yet, check if they sent a join request recorded in DB
            if is_channel_joined_in_db(str(user_id), ch_id):
                continue
            desc = str(res.get("description", "")).lower()
            if "not a member" in desc or "user not found" in desc:
                unjoined.append(ch)
            elif "chat not found" in desc or "bot is not a member" in desc or "chat_admin_required" in desc:
                logger.info(f"Bot is not admin in channel {ch_id}. Skipping strict check for this placeholder channel.")
                continue

    return (len(unjoined) == 0, unjoined)


# ---------------------------------------------------------------------------
# 9. COMMAND & CALLBACK HANDLERS
# ---------------------------------------------------------------------------
def handle_start(chat_id, user: dict, args: list[str]):
    user_id = str(user.get("id"))
    name = user.get("first_name") or user.get("username") or "Friend"
    username = user.get("username") or ""

    ref_param = args[0] if len(args) > 0 else None
    referrer_id = None

    if ref_param:
        clean_ref = ref_param.replace("ref_", "").strip()
        if clean_ref.isdigit():
            referrer_id = clean_ref

    existing = get_user_from_db(user_id)
    blocked_record = db_request(f"blocked_accounts/{user_id}.json")
    is_blocked = bool(
        (existing and existing.get("deviceBlocked") is True)
        or (blocked_record is True or (isinstance(blocked_record, dict) and blocked_record.get("blocked") is True))
    )

    if referrer_id:
        if referrer_id == user_id:
            logger.info(f"Self-referral attempted by {user_id}")
            referrer_id = None
        elif is_blocked:
            logger.info(f"Blocked account referral ignored for {user_id}")
            referrer_id = None
        elif existing and (
            existing.get("referredBy")
            or existing.get("referralRewardGiven")
            or existing.get("hasScratchedFirstCard")
            or (existing.get("balance") or 0) > 0
            or (existing.get("friendsJoined") or 0) > 0
        ):
            logger.info(f"Existing user {user_id} cannot be referred by {referrer_id}")
            referrer_id = existing.get("referredBy")
        elif is_already_referred(referrer_id, user_id):
            logger.info(f"Duplicate referral attempted for {referrer_id} by {user_id}")
        else:
            # Also check circular referral: if user_id previously referred referrer_id
            ref_user_db = get_user_from_db(referrer_id)
            if ref_user_db and str(ref_user_db.get("referredBy") or "").strip() == user_id:
                logger.info(f"Circular referral blocked between {user_id} and {referrer_id}")
                referrer_id = None
            else:
                record_referral(referrer_id, user_id, name, username, status="pending_first_scratch")
                logger.info(f"Referral pending first scratch: {user_id} referred by {referrer_id}")

    if not existing:
        welcome_user = {
            "id": user_id,
            "telegramId": user_id,
            "name": name,
            "username": username,
            "balance": 0,
            "spins": 1,
            "friendsJoined": 0,
            "spinsEarned": 1,
            "claimedWelcomeSpin": True,
            "createdAt": int(time.time() * 1000),
            "isVerified": False,
            "deviceVerified": False,
            "deviceBlocked": is_blocked,
            "referredBy": referrer_id if (referrer_id and referrer_id != user_id) else None,
            "referralRewardGiven": False,
        }
        db_request(f"users/{user_id}.json", method="PUT", data=welcome_user)
        existing = welcome_user
    else:
        patch_data = {}
        # Guarantee 1 signup scratch card for any new/referred user who hasn't received or scratched their 1st card yet
        has_played_first = bool(
            existing.get("claimedWelcomeSpin") is True
            or (existing.get("balance") or 0) > 0
            or existing.get("hasScratchedFirstCard") is True
            or existing.get("referralRewardGiven") is True
        )
        if not has_played_first and (existing.get("spins") is None or int(existing.get("spins") or 0) < 1):
            patch_data["spins"] = 1
            patch_data["spinsEarned"] = max(int(existing.get("spinsEarned") or 0), 1)
            patch_data["claimedWelcomeSpin"] = True
            existing["spins"] = 1
            existing["spinsEarned"] = patch_data["spinsEarned"]
            existing["claimedWelcomeSpin"] = True

        if referrer_id and referrer_id != user_id and not existing.get("referredBy") and (existing.get("balance") or 0) == 0:
            patch_data["referredBy"] = referrer_id
            existing["referredBy"] = referrer_id

        if is_blocked:
            patch_data["deviceBlocked"] = True
            patch_data["isVerified"] = False
            patch_data["deviceVerified"] = False
            existing["deviceBlocked"] = True
            existing["isVerified"] = False
            existing["deviceVerified"] = False

        if patch_data:
            db_request(f"users/{user_id}.json", method="PATCH", data=patch_data)

    if is_blocked:
        send_message_smart(
            chat_id,
            f"{pe('🚫')} <b>Device Verification Failed / Account Blocked!</b>\n\n"
            f"Ek phone me sirf 1 account allow hai. Ye ID permanently block ho chuki hai.",
        )
        return

    # Always verify that user is still joined / has sent join request to all mandatory channels!
    # If user left any channel and presses /start again, force them to rejoin before showing Home page.
    all_joined, _ = check_user_channels(int(user_id))

    if all_joined and existing.get("isVerified") and existing.get("deviceVerified") and not existing.get("deviceBlocked"):
        app_url = f"{WEB_URL}/?uid={user_id}&start=ref_{referrer_id}" if referrer_id else f"{WEB_URL}/?uid={user_id}"
        verified_markup = {
            "inline_keyboard": [
                [pbtn("🎉 Click To Home", emoji_char="🎉", web_app={"url": app_url})],
                [pbtn("👥 Refer And Earn", emoji_char="👥", callback_data="my_invite")],
            ]
        }
        verified_text = (
            f"{pe('🔥')}<b>Congratulations Sussefuly Verfied {pe('✅')}</b>\n\n"
            f"{pe('🎉')} <b>Click To Home And Refer And Earn {pe('🎉')}</b>\n\n"
            f"{pe('😍')}{pe('😍')}<b>Now All Payment Instant {pe('😍')}{pe('😍')}</b>"
        )
        send_message_smart(chat_id, verified_text, reply_markup=verified_markup)
        return

    channels = load_channels()
    welcome_text = (
        f"{pe('🎁')} <b>Hey  Welcome To Scratch The Win !!</b>\n\n"
        f"{pe('🛫')} <b>Join  Channels Below To Continue{pe('🛫')}</b>\n\n"
        f"{pe('😍')} <b>After Joining Click Claim{pe('🚨')}</b>"
    )
    markup = build_channels_keyboard(channels, ref_param)
    send_message_smart(chat_id, welcome_text, reply_markup=markup)


def handle_claim_callback(query: dict):
    query_id = query.get("id")
    user = query.get("from") or {}
    msg = query.get("message") or {}
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    data = query.get("data") or ""

    user_id = str(user.get("id"))
    ref_param = None
    if data.startswith("claim_"):
        raw = data.replace("claim_", "")
        if raw != "none":
            ref_param = raw

    all_joined, _ = check_user_channels(int(user_id))
    if not all_joined:
        answer_callback_query(query_id, "⚠️ Kripya sabhi channels join karein (ya Join Request bhejein) fir Claim dabayein!", show_alert=True)
        return

    answer_callback_query(query_id)

    # Check if user already completed Step 2 Device Verification previously (e.g. rejoined after leaving channel)
    db_user = get_user_from_db(user_id) or {}
    if db_user.get("deviceBlocked") is True:
        answer_callback_query(
            query_id,
            "🚫 Device Verification Failed! Ye account permanently block ho chuka hai.",
            show_alert=True,
        )
        return

    if db_user.get("deviceVerified") and db_user.get("isVerified"):
        app_url = f"{WEB_URL}/?uid={user_id}&start={ref_param}" if ref_param else f"{WEB_URL}/?uid={user_id}"
        final_markup = {
            "inline_keyboard": [
                [pbtn("🎉 Click To Home", emoji_char="🎉", web_app={"url": app_url})],
                [pbtn("👥 Refer And Earn", emoji_char="👥", callback_data="my_invite")],
            ]
        }
        final_text = (
            f"{pe('🔥')}<b>Congratulations Sussefuly Verfied {pe('✅')}</b>\n\n"
            f"{pe('🎉')} <b>Click To Home And Refer And Earn {pe('🎉')}</b>\n\n"
            f"{pe('😍')}{pe('😍')}<b>Now All Payment Instant {pe('😍')}{pe('😍')}</b>"
        )
        edit_message_text_smart(chat_id, message_id, final_text, reply_markup=final_markup)
        return

    verify_url = f"{WEB_URL}/?verify=true&uid={user_id}"
    if ref_param:
        verify_url = f"{WEB_URL}/?verify=true&uid={user_id}&start={ref_param}"

    step2_markup = {
        "inline_keyboard": [
            [pbtn("🍑 Please Click Verify Device 🎉", emoji_char="🍑", web_app={"url": verify_url})],
            [pbtn("🔄 Check Status", emoji_char="🔄", callback_data=f"check_device_{ref_param or 'none'}")],
        ]
    }
    step2_text = (
        f"{pe('🎁')}<b>All Channel Verfied Done {pe('🔥')}{pe('👌')}</b>\n\n"
        f"{pe('⚠️')}<b>Step 2:- Device verification</b> \n\n"
        f"{pe('🍑')} <b>Please Click Verify Device {pe('🎉')}</b>"
    )
    edit_message_text_smart(chat_id, message_id, step2_text, reply_markup=step2_markup)


def handle_check_device_callback(query: dict):
    query_id = query.get("id")
    user = query.get("from") or {}
    msg = query.get("message") or {}
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    data = query.get("data") or ""

    user_id = str(user.get("id"))
    ref_param = None
    if data.startswith("check_device_"):
        raw = data.replace("check_device_", "")
        if raw != "none":
            ref_param = raw

    # Also ensure user hasn't left any channel before unlocking Home
    all_joined, _ = check_user_channels(int(user_id))
    if not all_joined:
        answer_callback_query(
            query_id,
            "⚠️ Aapne channel leave kar diya hai! Kripya sabhi channels wapas join karein.",
            show_alert=True,
        )
        channels = load_channels()
        welcome_text = (
            f"{pe('🎁')} <b>Hey  Welcome To Scratch The Win !!</b>\n\n"
            f"{pe('🛫')} <b>Join  Channels Below To Continue{pe('🛫')}</b>\n\n"
            f"{pe('😍')} <b>After Joining Click Claim{pe('🚨')}</b>"
        )
        markup = build_channels_keyboard(channels, ref_param)
        edit_message_text_smart(chat_id, message_id, welcome_text, reply_markup=markup)
        return

    db_user = get_user_from_db(user_id) or {}
    if db_user.get("deviceBlocked") is True:
        answer_callback_query(
            query_id,
            "🚫 Device Verification Failed! Ye account permanently block ho chuka hai.",
            show_alert=True,
        )
        return

    is_device_verified = db_user.get("deviceVerified") and db_user.get("isVerified")

    if not is_device_verified:
        answer_callback_query(
            query_id,
            "⚠️ Please click 'Verify Device' button first to complete step 2!",
            show_alert=True,
        )
        return

    answer_callback_query(query_id)
    app_url = f"{WEB_URL}/?uid={user_id}&start={ref_param}" if ref_param else f"{WEB_URL}/?uid={user_id}"
    final_markup = {
        "inline_keyboard": [
            [pbtn("🎉 Click To Home", emoji_char="🎉", web_app={"url": app_url})],
            [pbtn("👥 Refer And Earn", emoji_char="👥", callback_data="my_invite")],
        ]
    }
    final_text = (
        f"{pe('🔥')}<b>Congratulations Sussefuly Verfied {pe('✅')}</b>\n\n"
        f"{pe('🎉')} <b>Click To Home And Refer And Earn {pe('🎉')}</b>\n\n"
        f"{pe('😍')}{pe('😍')}<b>Now All Payment Instant {pe('😍')}{pe('😍')}</b>"
    )
    edit_message_text_smart(chat_id, message_id, final_text, reply_markup=final_markup)


def handle_invite(chat_id, user: dict):
    user_id = str(user.get("id"))
    bot_info = get_bot_info()
    bot_user = bot_info.get("username") or BOT_USERNAME
    invite_link = f"https://t.me/{bot_user}?start=ref_{user_id}"

    db_user = get_user_from_db(user_id) or {}
    spins = db_user.get("spins", 1)
    friends = db_user.get("friendsJoined", 0)

    share_text = urllib.parse.quote(
        f"🎁 Scratch The Win par Scratch Card khelo & Win Up to ₹50 Cash! 1 Sign Up = 1 Scratch & 1 Refer = 1 Scratch! 👇\n{invite_link}"
    )
    share_url = f"https://t.me/share/url?url={invite_link}&text={share_text}"

    markup = {
        "inline_keyboard": [
            [pbtn("🚀 Share Invite Link", emoji_char="🚀", url=share_url)],
            [pbtn("🎉 Click To Home (Win Up to ₹50)", emoji_char="🎉", web_app={"url": f"{WEB_URL}/?uid={user_id}"})],
        ]
    }

    msg = (
        f"{pe('🎉')} <b>Scratch &amp; Win Up to ₹50 - Refer And Earn</b> {pe('🎉')}\n\n"
        f"{pe('🔗')} <b>Your Personal Invite Link:</b>\n"
        f"<code>{invite_link}</code>\n\n"
        f"{pe('🎁')} <b>Rewards:</b>\n"
        f"• <b>1 Sign Up = 1 Free Scratch Card</b> (Win Up to ₹50)\n"
        f"• <b>1 Refer = 1 Free Scratch Card</b> (Jab friend 1st card scratch kare)\n"
        f"• {pe('✅')}{pe('✅')} <b>Now All Payment Instant</b> {pe('✅')}{pe('✅')}\n\n"
        f"{pe('📊')} <b>Your Stats:</b>\n"
        f"• Friends Joined: <b>{friends}</b>\n"
        f"• Available Scratch Cards: <b>{spins}</b>"
    )
    send_message_smart(chat_id, msg, reply_markup=markup)


def handle_help(chat_id):
    text = (
        f"{pe('👑')} <b>SCRATCH THE WIN - HELP & GUIDE</b> {pe('👑')}\n\n"
        f"1. <b>/start</b> - App start karein aur channels join karein\n"
        f"2. <b>/invite</b> - Apna personal referral link paayein (+1 Scratch per invite)\n\n"
        f"{pe('🔥')} <b>Congratulations Sussefuly Verfied {pe('✅')}</b>\n"
        f"{pe('🎉')} <b>Click To Home And Refer And Earn {pe('🎉')}</b>\n"
        f"{pe('✅')}{pe('✅')} <b>Now All Payment Instant {pe('✅')}{pe('✅')}</b>"
    )
    send_message_smart(chat_id, text)


def handle_ownerhelp(chat_id, user: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ Permission denied!")
        return
    text = (
        f"{pe('👑')} <b>OWNER ADMIN COMMANDS</b> {pe('👑')}\n\n"
        f"• <b>/channels</b> - Active mandatory channels list dekhein\n"
        f"• <b>/addchannel &lt;chat_id_or_@username&gt; &lt;name&gt; &lt;url&gt;</b> - Naya channel add karein\n"
        f"• <b>/removechannel &lt;chat_id_or_username&gt;</b> - Channel remove karein\n"
        f"• <b>/setemojis</b> (Reply karke) - ✨ Apne pasand ke Premium Animated Emojis bot ke replies/buttons me set karein\n"
        f"• <b>/emojitest</b> (Reply karke) - 🧪 Telegram Premium animated custom emojis preview test karein\n"
        f"• <b>/broadcast</b> (Reply karke) - 💎 Telegram Premium custom emojis & media sabhi users ko bhejein\n"
        f"• <b>/broadcast &lt;text&gt;</b> - Direct broadcast\n"
        f"• <b>/stats</b> - Total users & referrals check karein"
    )
    send_message_smart(chat_id, text)


def handle_setemojis(chat_id, user: dict, message: dict):
    """
    Allows the owner to reply to any message containing their favorite Telegram Premium
    animated emojis with /setemojis to automatically bind those custom_emoji_ids to the bot's replies & buttons.
    """
    if not is_owner(user):
        send_message(chat_id, "❌ Permission denied!")
        return

    target_msg = message.get("reply_to_message") or message
    full_text = target_msg.get("text") or target_msg.get("caption") or ""
    entities = target_msg.get("entities") or target_msg.get("caption_entities") or []
    utf16_bytes = full_text.encode("utf-16-le")

    updated = {}
    for ent in entities:
        if ent.get("type") == "custom_emoji" and ent.get("custom_emoji_id"):
            offset = ent.get("offset", 0)
            length = ent.get("length", 0)
            cid = str(ent["custom_emoji_id"]).strip()
            try:
                underlying_char = utf16_bytes[offset * 2 : (offset + length) * 2].decode("utf-16-le").strip()
                if underlying_char:
                    _PREMIUM_EMOJI_MAP[underlying_char] = cid
                    updated[underlying_char] = cid
                    if underlying_char in ("✅", "☑️", "✔️", "✔"):
                        _PREMIUM_EMOJI_MAP["✅"] = cid
                        _PREMIUM_EMOJI_MAP["✔"] = cid
                        updated["✅"] = cid
                        updated["✔"] = cid
            except Exception:
                continue

    if not updated:
        send_message_smart(
            chat_id,
            f"{pe('👑')} <b>CUSTOM PREMIUM EMOJI SETTER</b>\n\n"
            f"Apne Telegram Premium se koi bhi animated emojis (jaise 👑 🌺 😍 ✅ 🔥 🎉 🍑 👥 🚀) ek message me bhejein aur us message ko <b>Reply</b> karke <code>/setemojis</code> likhein!\n\n"
            f"Bot turant unki exact <code>custom_emoji_id</code> save kar lega aur har reply + button me wahi animated emojis bhejega!",
        )
        return

    db_request("bot_config/premium_emojis.json", method="PATCH", data=updated)
    summary = "\n".join([f"• <tg-emoji emoji-id=\"{cid}\">{em}</tg-emoji> (<code>{cid}</code>)" for em, cid in updated.items()])
    send_message_smart(
        chat_id,
        f"{pe('✅')} <b>{len(updated)} Premium Animated Emojis Updated in Bot!</b>\n\n{summary}",
    )


def handle_stats(chat_id, user: dict):
    if not is_owner(user):
        return
    users = db_request("users.json") or {}
    referrals = db_request("referrals.json") or {}
    total_users = len(users) if isinstance(users, dict) else len(users or [])
    total_refs = len(referrals) if isinstance(referrals, dict) else len(referrals or [])

    text = (
        f"{pe('📊')} <b>BOT LIVE STATS</b> {pe('📊')}\n\n"
        f"{pe('👥')} Total Registered Users: <b>{total_users}</b>\n"
        f"{pe('🔗')} Active Referrals: <b>{total_refs}</b>\n"
        f"{pe('🚀')} Web App URL: <code>{WEB_URL}</code>\n"
        f"{pe('✅')} Server Status: <b>Online 24/7</b>"
    )
    send_message_smart(chat_id, text)


def handle_channels(chat_id, user: dict):
    if not is_owner(user):
        return
    channels = load_channels()
    if not channels:
        send_message_smart(chat_id, f"{pe('⚠️')} Koi channels configured nahi hain! Use <code>/addchannel</code>")
        return

    lines = [f"{pe('👑')} <b>ACTIVE CHANNELS ({len(channels)}):</b>\n"]
    for idx, ch in enumerate(channels, 1):
        lines.append(
            f"{idx}. <b>{ch.get('name', 'Channel')}</b>\n"
            f"   ID: <code>{ch.get('id')}</code>\n"
            f"   URL: {ch.get('url')}"
        )
    lines.append("\n💡 <i>To add: /addchannel &lt;id&gt; &lt;name&gt; &lt;url&gt;</i>")
    lines.append("💡 <i>To remove: /removechannel &lt;id&gt;</i>")
    send_message_smart(chat_id, "\n\n".join(lines))


def handle_addchannel(chat_id, user: dict, args: list[str]):
    if not is_owner(user):
        send_message_smart(chat_id, f"{pe('🚫')} Permission denied!")
        return
    if len(args) < 3:
        send_message_smart(
            chat_id,
            f"{pe('⚠️')} <b>Usage:</b>\n"
            "<code>/addchannel &lt;chat_id_or_@username&gt; &lt;name&gt; &lt;url&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/addchannel @mychannel VIP Official Channel https://t.me/mychannel</code>",
        )
        return

    ch_id = args[0].strip()
    url = args[-1].strip()
    name = " ".join(args[1:-1]).strip()

    channel_obj = {
        "id": ch_id,
        "name": name,
        "url": url,
        "is_private": ch_id.startswith("-100") or "t.me/+" in url,
        "createdAt": int(time.time() * 1000),
    }

    clean_key = re.sub(r"[^a-zA-Z0-9_-]", "_", ch_id)
    db_request(f"bot_config/channels/{clean_key}.json", method="PUT", data=channel_obj)

    global _CHANNELS_CACHE
    _CHANNELS_CACHE = []
    load_channels()

    send_message_smart(
        chat_id,
        f"{pe('✅')} <b>Channel Added Successfully!</b>\n\n"
        f"{pe('👑')} <b>Name:</b> {name}\n"
        f"{pe('🔗')} <b>ID:</b> <code>{ch_id}</code>\n"
        f"{pe('🚀')} <b>URL:</b> {url}",
    )


def handle_removechannel(chat_id, user: dict, args: list[str]):
    if not is_owner(user):
        send_message_smart(chat_id, f"{pe('🚫')} Permission denied!")
        return
    if not args:
        send_message_smart(
            chat_id,
            f"{pe('⚠️')} <b>Usage:</b> <code>/removechannel &lt;chat_id_or_username&gt;</code>\n"
            "Use <code>/channels</code> to see the list.",
        )
        return

    target_id = args[0].strip()
    clean_key = re.sub(r"[^a-zA-Z0-9_-]", "_", target_id)
    db_request(f"bot_config/channels/{clean_key}.json", method="DELETE")

    global _CHANNELS_CACHE, PERMANENT_CHANNELS
    PERMANENT_CHANNELS = [
        c for c in PERMANENT_CHANNELS if str(c.get("id")) != target_id and str(c.get("url")) != target_id
    ]
    _CHANNELS_CACHE = []
    load_channels()

    send_message_smart(chat_id, f"{pe('✅')} <b>Channel {target_id} Removed Successfully!</b>")


def handle_emojitest(chat_id, user: dict, message: dict):
    if not is_owner(user):
        send_message_smart(chat_id, f"{pe('🚫')} Permission denied!")
        return
    reply_msg = message.get("reply_to_message")
    if reply_msg:
        custom_count = len([e for e in (reply_msg.get("entities") or reply_msg.get("caption_entities") or []) if e.get("type") == "custom_emoji"])
        send_message_smart(
            chat_id,
            f"{pe('🔥')} <b>PREMIUM EMOJI TEST PREVIEW ({custom_count} Custom Emojis Detected):</b>\n"
            f"Niche aapka message 100% original Premium Animated Emojis ke saath aa raha hai 👇",
        )
        res = deliver_premium_message(chat_id, chat_id, reply_msg)
        if res.get("ok"):
            send_message_smart(
                chat_id,
                f"{pe('✅')} <b>Premium Custom Emojis Verified!</b>\n"
                "Ab usi message ko <b>Reply</b> karke <code>/broadcast</code> likhein — sabhi users ko exact animated premium emojis jayenge!",
            )
        else:
            send_message_smart(chat_id, f"{pe('⚠️')} Test preview failed: {res.get('description')}")
    else:
        send_message_smart(
            chat_id,
            f"{pe('🔥')} <b>EMOJI & MEDIA TEST GUIDE:</b>\n\n"
            "Apne Telegram Premium animated emojis wale message ko <b>Reply</b> karein aur likhein: <code>/emojitest</code>",
        )


def extract_shifted_entities(full_text: str, entities: list[dict], prefix_str: str) -> list[dict]:
    """
    Adjusts UTF-16 entity offsets when stripping '/broadcast ' command prefix so
    custom_emoji entities sent directly inside '/broadcast <text>' remain 100% intact.
    """
    if not entities:
        return []
    prefix_utf16_len = len(prefix_str.encode("utf-16-le")) // 2
    shifted = []
    for ent in entities:
        offset = ent.get("offset", 0)
        if offset >= prefix_utf16_len:
            new_ent = dict(ent)
            new_ent["offset"] = offset - prefix_utf16_len
            shifted.append(new_ent)
    return shifted


def handle_broadcast(chat_id, user: dict, message: dict):
    if not is_owner(user):
        return
    reply_msg = message.get("reply_to_message")
    full_text = message.get("text") or message.get("caption") or ""
    command_match = re.match(r"^/broadcast(@\w+)?\s*", full_text)
    prefix_len = command_match.end() if command_match else 0
    prefix_str = full_text[:prefix_len]
    direct_text = full_text[prefix_len:]

    if not reply_msg and not direct_text.strip():
        send_message_smart(
            chat_id,
            f"{pe('👑')} <b>PREMIUM BROADCAST GUIDE:</b>\n\n"
            "1. Apne custom animated emojis, photos, ya media wale message ko <b>Reply</b> karein aur likhein: <code>/broadcast</code> (Recommended for 100% Premium Emojis)\n"
            "2. Direct bhejne ke liye: <code>/broadcast &lt;message&gt;</code>",
        )
        return

    raw_entities = message.get("entities") or message.get("caption_entities") or []
    shifted_entities = extract_shifted_entities(full_text, raw_entities, prefix_str)
    direct_has_custom_emoji = any(e.get("type") == "custom_emoji" for e in shifted_entities)

    users = db_request("users.json") or {}
    items = list(users.values()) if isinstance(users, dict) else list(users or [])

    valid_user_ids = []
    seen = set()
    for u in items:
        if isinstance(u, dict) and u.get("id"):
            try:
                uid = int(u["id"])
                if uid not in seen:
                    seen.add(uid)
                    valid_user_ids.append(uid)
            except Exception:
                continue

    if not valid_user_ids:
        send_message_smart(chat_id, f"{pe('⚠️')} Database me koi users nahi mile!")
        return

    send_message_smart(chat_id, f"{pe('🚀')} Premium Broadcast shuru ho raha hai {len(valid_user_ids)} users ko...")

    sent = 0
    failed = 0
    for uid in valid_user_ids:
        if reply_msg:
            res = deliver_premium_message(uid, chat_id, reply_msg)
        elif direct_has_custom_emoji:
            # Send with exact UTF-16 shifted custom_emoji entities (no parse_mode conflict)
            res = tg_api(
                "sendMessage",
                {
                    "chat_id": uid,
                    "text": direct_text,
                    "entities": shifted_entities,
                },
            )
            if not res.get("ok"):
                res = forward_message(uid, chat_id, message.get("message_id"))
        else:
            res = send_message(uid, direct_text.strip())
            if not res.get("ok"):
                res = send_message(uid, direct_text.strip(), parse_mode="")
        if res.get("ok"):
            sent += 1
        else:
            failed += 1
        time.sleep(0.04)

    send_message_smart(
        chat_id,
        f"{pe('✅')} <b>Broadcast Completed!</b>\nDelivered: <b>{sent}</b> | Failed/Blocked: <b>{failed}</b>",
    )


# ---------------------------------------------------------------------------
# 10. UPDATE ROUTER & LONG-POLLING LOOP
# ---------------------------------------------------------------------------
def process_update(upd: dict):
    try:
        # 1. Handle Chat Join Request (Private Channels - Record request only, NO Auto-Approve)
        if "chat_join_request" in upd:
            req = upd["chat_join_request"]
            user_id = str(req.get("from", {}).get("id", ""))
            chat_id = str(req.get("chat", {}).get("id", ""))
            if user_id and chat_id:
                record_channel_joined(user_id, chat_id)
            return

        # 1b. Handle Chat Member Status Change (Detect when user leaves/is kicked or joins a channel)
        if "chat_member" in upd:
            cm = upd["chat_member"]
            chat_id = str(cm.get("chat", {}).get("id", ""))
            new_m = cm.get("new_chat_member") or {}
            user_id = str((new_m.get("user") or {}).get("id", ""))
            status = new_m.get("status", "")
            if user_id and chat_id:
                if status in ["left", "kicked"]:
                    remove_channel_joined(user_id, chat_id)
                elif status in ["member", "administrator", "creator", "restricted"]:
                    record_channel_joined(user_id, chat_id)
            return

        # 2. Handle Callback Query (Inline Buttons)
        if "callback_query" in upd:
            query = upd["callback_query"]
            data = query.get("data") or ""
            if data.startswith("claim_"):
                handle_claim_callback(query)
            elif data.startswith("check_device_"):
                handle_check_device_callback(query)
            elif data == "my_invite":
                answer_callback_query(query.get("id"))
                chat_id = query.get("message", {}).get("chat", {}).get("id")
                handle_invite(chat_id, query.get("from") or {})
            return

        # 3. Handle Standard Messages & Commands
        msg = upd.get("message")
        if not msg:
            return

        chat_id = msg.get("chat", {}).get("id")
        user = msg.get("from") or {}
        text = (msg.get("text") or msg.get("caption") or "").strip()

        if not text.startswith("/"):
            return

        parts = text.split()
        cmd = parts[0].split("@")[0].lower()
        args = parts[1:]

        if cmd == "/start":
            handle_start(chat_id, user, args)
        elif cmd in ["/invite", "/refer"]:
            handle_invite(chat_id, user)
        elif cmd == "/help":
            handle_help(chat_id)
        elif cmd == "/ownerhelp":
            handle_ownerhelp(chat_id, user)
        elif cmd == "/stats":
            handle_stats(chat_id, user)
        elif cmd == "/channels":
            handle_channels(chat_id, user)
        elif cmd == "/addchannel":
            handle_addchannel(chat_id, user, args)
        elif cmd == "/removechannel":
            handle_removechannel(chat_id, user, args)
        elif cmd == "/setemojis":
            handle_setemojis(chat_id, user, msg)
        elif cmd == "/emojitest":
            handle_emojitest(chat_id, user, msg)
        elif cmd == "/broadcast":
            handle_broadcast(chat_id, user, msg)
    except Exception as e:
        logger.error(f"Error processing update: {e}")


def main():
    logger.info("====================================================")
    logger.info("🚀 Starting Scratch The Win Bot (Pure Python Engine)")
    logger.info(f"🌐 Mini App URL: {WEB_URL}")
    logger.info("====================================================")

    # Start 24/7 HTTP Health Check Server
    t = threading.Thread(target=start_health_server, daemon=True)
    t.start()

    # Load live Telegram Premium Animated Emoji IDs
    init_premium_emojis()

    # Delete any active webhook & drop pending updates
    tg_api("deleteWebhook", {"drop_pending_updates": True})
    bot_me = get_bot_info()
    logger.info(f"✅ Bot Connected: @{bot_me.get('username', BOT_USERNAME)} (ID: {bot_me.get('id')})")

    offset = 0
    while True:
        try:
            res = tg_api(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["message", "callback_query", "chat_join_request", "chat_member"],
                },
                timeout=35,
            )
            if res.get("ok") and isinstance(res.get("result"), list):
                for upd in res["result"]:
                    offset = upd["update_id"] + 1
                    process_update(upd)
            else:
                desc = res.get("description", "")
                if "conflict" in str(desc).lower():
                    logger.warning("⚠️ Another bot instance is polling. Retrying in 5s...")
                    time.sleep(5)
                else:
                    time.sleep(2)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.warning(f"Polling loop notice: {e}. Retrying in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    main()
