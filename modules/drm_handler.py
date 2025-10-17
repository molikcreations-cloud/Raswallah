drm_handler_full.py

Fully merged DRM handler with global token, automatic refresh, logging configuration,

integrated signing function, and scheduled async refresh for Classplus DRM links.

import os import time import json import asyncio import requests import logging import globals  # uses global cptoken variable

--------------------------

Logging Configuration

--------------------------

def setup_logging(level=logging.INFO): logging.basicConfig( level=level, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d-%b-%y %H:%M:%S' ) logger = logging.getLogger(name) return logger

logger = setup_logging()

--------------------------

Global Constants

--------------------------

MAX_SIGN_RETRIES = 3 SIGN_RETRY_DELAY = 2 REFRESH_INTERVAL_HOURS = 5  # refresh every 5 hours automatically VERCEL_SIGN_API = "https://sainibotsdrm.vercel.app/api" CLASSPLUS_LOGIN_API = "https://api.classplusapp.com/api/v2/login"

--------------------------

Signing & Token Handling

--------------------------

def get_signed_url_via_vercel(mpd_url: str, token: str): params = { 'url': mpd_url, 'token': token, 'auth': '4443683167' } try: res = requests.get(VERCEL_SIGN_API, params=params, timeout=15) res.raise_for_status() data = res.json() except Exception as e: raise Exception(f"Failed contacting signing service: {e}")

if not data:
    raise Exception("Empty response from signing service")

if 'error' in data:
    raise Exception(data['error'])

return data

def refresh_cptoken_via_login(): mobile = os.environ.get('CLASSPLUS_MOBILE') password = os.environ.get('CLASSPLUS_PASSWORD')

if not mobile or not password:
    raise Exception("Missing Classplus credentials. Set CLASSPLUS_MOBILE and CLASSPLUS_PASSWORD.")

payload = {'mobile': mobile, 'password': password}
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

try:
    resp = requests.post(CLASSPLUS_LOGIN_API, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    j = resp.json()
    token = j.get('data', {}).get('token') or j.get('token') or j.get('access_token')
    if not token:
        raise Exception(f"Login succeeded but token not found in response: {j}")
    globals.cptoken = token
    logger.info("✅ Classplus token refreshed successfully.")
    return token
except Exception as e:
    raise Exception(f"Failed to refresh Classplus token: {e}")

def sign_and_get_mpd(mpd_url: str): attempts = 0 last_exc = None local_token = globals.cptoken

while attempts < MAX_SIGN_RETRIES:
    attempts += 1
    try:
        data = get_signed_url_via_vercel(mpd_url, local_token)
        if data.get('url'):
            keys = data.get('keys') or []
            return data['url'], keys
        raise Exception(f"Unexpected response payload: {data}")
    except Exception as exc:
        last_exc = exc
        msg = str(exc)
        logger.warning(f"Signing attempt {attempts} failed: {msg}")

        if 'expired' in msg.lower() or 'token' in msg.lower():
            try:
                new_token = refresh_cptoken_via_login()
                local_token = new_token
                globals.cptoken = new_token
                continue
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                raise Exception(f"Signing failed and token could not be refreshed: {e}")

        time.sleep(SIGN_RETRY_DELAY)

raise Exception(f"Failed to sign URL after {MAX_SIGN_RETRIES} attempts. Last error: {last_exc}")

--------------------------

Integrated Download Handler

--------------------------

async def handle_classplus_download(bot, channel_id, name, original_url): try: mpd, keys = sign_and_get_mpd(original_url) keys_string = " ".join([f"--key {k}" for k in keys]) if keys else None return mpd, keys_string except Exception as e: await bot.send_message( channel_id, f"⚠️Downloading Failed⚠️\nName =>> {name}\nUrl =>> {original_url}\n\n<blockquote expandable><i><b>Failed Reason to sign url: {str(e)}</b></i></blockquote>", disable_web_page_preview=True ) logger.error(f"❌ Download failed for {name}: {e}") return None, None

--------------------------

Async Background Token Refresh

--------------------------

async def schedule_token_refresh(): while True: try: logger.info("🔄 Scheduled token refresh triggered.") refresh_cptoken_via_login() except Exception as e: logger.error(f"Scheduled token refresh failed: {e}") await asyncio.sleep(REFRESH_INTERVAL_HOURS * 3600)

async def start_background_tasks(): asyncio.create_task(schedule_token_refresh()) logger.info(f"🚀 Background token refresh scheduler started. Interval: {REFRESH_INTERVAL_HOURS} hours.")

--------------------------

Usage Example

--------------------------

import asyncio

asyncio.run(start_background_tasks())

mpd, keys = await handle_classplus_download(bot, channel_id, name, url)

if mpd:

print("Signed URL:", mpd)

print("Keys:", keys)

else:

print("Download failed.")

