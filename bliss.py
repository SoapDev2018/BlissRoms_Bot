from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
import json
import httpx
import datetime
import humanfriendly
import html
from typing import Final, Dict, Optional, List, Tuple
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import asyncio

# YAML Helper
def load_config(filename):
    with open(filename, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

config_data = load_config("config.yml")
telegram_config = config_data["telegram"]
bliss_config = config_data["bliss"]

# Constants
API_ID: Final[int] = int(telegram_config["api_id"])
API_HASH: Final[str] = telegram_config["api_hash"]
BOT_TOKEN: Final[str] = telegram_config["bot_token"]
AUTHORIZED_IDS: Final[List[int]] = [int(telegram_id) for telegram_id in telegram_config["authorized_ids"] if telegram_id is not None]
DOWNLOAD_BASE_URL: Final[str] = bliss_config["download_url"]
RQST_USER_AGENT: Final[str] = bliss_config["user_agent"]
DEFAULT_RQST_USER_AGENT: Final[str] = bliss_config["default_user_agent"]
TELEGRAM_GROUP_IDS: Final[List[int]] = [int(group_id) for group_id in telegram_config.get("group_ids") if group_id is not None]

# Pyrogram Client
app = Client("BlissBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Scheduled Jobs
async def download_devices_job() -> None:
    devices_file = "devices.json"
    devices_url = "https://raw.githubusercontent.com/BlissRoms-Devices/official-devices/main/devices.json"
    if os.path.isfile(devices_file):
        if RQST_USER_AGENT:
            headers = {"User-Agent": RQST_USER_AGENT}
        else:
            headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
        new_devices_file = "new_devices.json"
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(devices_url)
            if response.status_code != 200:
                print(f"Request failed with status code: {response.status_code}")
                return None
            with open(new_devices_file, "w") as f:
                json.dump(json.loads(response.text), f)
        if os.path.getsize(devices_file) != os.path.getsize(new_devices_file):
            os.remove(devices_file)
            os.rename(new_devices_file, devices_file)
        else:
            os.remove(new_devices_file)
    else:
        async with httpx.AsyncClient() as client:
            response = await client.get(devices_url)
            if response.status_code != 200:
                print(f"Request failed with status code: {response.status_code}")
                return None
            with open(devices_file, "w") as f:
                json.dump(json.loads(response.text), f)

# Helper Functions
async def devices_list() -> Optional[Dict[str, Dict[str, str]]]:
    devices_file = "devices.json"
    devices: Dict[str, str] = {}
    try:
        with open(devices_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        devices_url = "https://raw.githubusercontent.com/BlissRoms-Devices/official-devices/main/devices.json"
        if RQST_USER_AGENT:
            headers = {"User-Agent": RQST_USER_AGENT}
        else:
            headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(devices_url)
            if response.status_code != 200:
                print(f"Request failed with status code: {response.status_code}")
                return None
            data = json.loads(response.text)
            with open(devices_file, "w") as f:
                json.dump(data, f)
    for device in data:
        device_data: Dict[str, str] = {
            'brand': device['brand'],
            'name': device['name'],
            'maintainer': device['supported_versions'][0]['maintainer_name'],
            'support': device['supported_versions'][0]['support_thread'],
        }
        device_codename: str = device['codename']
        devices[device_codename] = device_data
    return devices

async def get_device_info(device_codename: str) -> Optional[Dict[str, str]]:
    devices_file = "devices.json"
    try:
        with open(devices_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        await download_devices_job()
    for device in data:
        if device['codename'] != device_codename:
            continue
        return {
            'brand': device['brand'],
            'name': device['name'],
            'maintainer': device['supported_versions'][0]['maintainer_name'],
            'support': device['supported_versions'][0]['support_thread'],
        }
    
async def get_vanilla_build(device_codename: str) -> Optional[Dict[str, str]]:
    download_url = DOWNLOAD_BASE_URL.format(device_codename, "vanilla")
    build_data: Dict[str, str] = {}
    if RQST_USER_AGENT:
        headers = {"User-Agent": RQST_USER_AGENT}
    else:
        headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(download_url)
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return None
        device_data = json.loads(response.text)['response'][0]
        build_data = {
            'date': datetime.datetime.fromtimestamp(device_data['datetime']).strftime('%d-%m-%Y'),
            'size': humanfriendly.format_size(device_data['size']),
            'version': device_data['version'],
            'url': device_data['url'],
        }
        return build_data
    
async def get_gapps_build(device_codename: str) -> Optional[Dict[str, str]]:
    download_url = DOWNLOAD_BASE_URL.format(device_codename, "gapps")
    build_data: Dict[str, str] = {}
    if RQST_USER_AGENT:
        headers = {"User-Agent": RQST_USER_AGENT}
    else:
        headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(download_url)
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return None
        device_data = json.loads(response.text)['response'][0]
        build_data = {
            'date': datetime.datetime.fromtimestamp(device_data['datetime']).strftime('%d-%m-%Y'),
            'size': humanfriendly.format_size(device_data['size']),
            'version': device_data['version'],
            'url': device_data['url'],
        }
        return build_data

async def get_pixelgapps_build(device_codename: str) -> Optional[Dict[str, str]]:
    download_url = DOWNLOAD_BASE_URL.format(device_codename, "pixelgapps")
    build_data: Dict[str, str] = {}
    if RQST_USER_AGENT:
        headers = {"User-Agent": RQST_USER_AGENT}
    else:
        headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(download_url)
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return None
        device_data = json.loads(response.text)['response'][0]
        build_data = {
            'date': datetime.datetime.fromtimestamp(device_data['datetime']).strftime('%d-%m-%Y'),
            'size': humanfriendly.format_size(device_data['size']),
            'version': device_data['version'],
            'url': device_data['url'],
        }
        return build_data

async def get_foss_build(device_codename: str) -> Optional[Dict[str, str]]:
    download_url = DOWNLOAD_BASE_URL.format(device_codename, "foss")
    build_data: Dict[str, str] = {}
    if RQST_USER_AGENT:
        headers = {"User-Agent": RQST_USER_AGENT}
    else:
        headers = {"User-Agent": DEFAULT_RQST_USER_AGENT}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(download_url)
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return None
        device_data = json.loads(response.text)['response'][0]
        build_data = {
            'date': datetime.datetime.fromtimestamp(device_data['datetime']).strftime('%d-%m-%Y'),
            'size': humanfriendly.format_size(device_data['size']),
            'version': device_data['version'],
            'url': device_data['url'],
        }
        return build_data

# Pyrogram Helper Functions
def get_build_keyboard(vanilla_build_url: str, gapps_build_url: str, pixelgapps_build_url: str, foss_build_url: str, device_codename: str) -> Optional[InlineKeyboardMarkup]:
    blank_keyboard = []
    if vanilla_build_url:
        blank_keyboard.append([InlineKeyboardButton(text=f"Download Vanilla Build ({device_codename})", url=vanilla_build_url)])
    if gapps_build_url:
        blank_keyboard.append([InlineKeyboardButton(text=f"Download Gapps Build ({device_codename})", url=gapps_build_url)])
    if pixelgapps_build_url:
        blank_keyboard.append([InlineKeyboardButton(text=f"Download Pixel Gapps Build ({device_codename})", url=pixelgapps_build_url)])
    if foss_build_url:
        blank_keyboard.append([InlineKeyboardButton(text=f"Download FOSS Build ({device_codename})", url=foss_build_url)])
    if len(blank_keyboard) > 0:
        blank_keyboard.append([InlineKeyboardButton("Close", callback_data="close")])
    else:
        return None

    build_keyboard = InlineKeyboardMarkup(
        blank_keyboard
    )
    return build_keyboard

def get_device_text(device_vanilla_build: Optional[Dict[str, str]], device_gapps_build: Optional[Dict[str, str]], device_pixelgapps_build: Optional[Dict[str, str]], device_foss_build: Optional[Dict[str, str]], device_data: Optional[Dict[str, str]], device_codename: str) -> Tuple[str, Optional[InlineKeyboardMarkup], bool]:
    build_found = False
    if not device_data:
        device_text = ""
    else:
        device_text = f"<strong>Device:</strong> {device_data.get('brand')} {device_data.get('name')}\n<strong>Maintainer:</strong> {device_data.get('maintainer')}\n<strong>Support:</strong> {device_data.get('support')}\n\n"
        if device_vanilla_build:
            build_found = True
            device_text += f"<strong>Build Type:</strong> Vanilla\n<strong>Build Date:</strong> {device_vanilla_build.get('date')}\n<strong>Build Size:</strong> {device_vanilla_build.get('size')}\n<strong>Build Version:</strong> {device_vanilla_build.get('version')}\n\n"
        if device_gapps_build:
            build_found = True
            device_text += f"<strong>Build Type:</strong> GApps\n<strong>Build Date:</strong> {device_gapps_build.get('date')}\n<strong>Build Size:</strong> {device_gapps_build.get('size')}\n<strong>Build Version:</strong> {device_gapps_build.get('version')}"
        if device_pixelgapps_build:
            build_found = True
            device_text += f"<strong>Build Type:</strong> Pixel Gapps\n<strong>Build Date:</strong> {device_pixelgapps_build.get('date')}\n<strong>Build Size:</strong> {device_pixelgapps_build.get('size')}\n<strong>Build Version:</strong> {device_pixelgapps_build.get('version')}\n\n"
        if device_foss_build:
            build_found = True
            device_text += f"<strong>Build Type:</strong> FOSS\n<strong>Build Date:</strong> {device_foss_build.get('date')}\n<strong>Build Size:</strong> {device_foss_build.get('size')}\n<strong>Build Version:</strong> {device_foss_build.get('version')}\n\n"
        build_keyboard = get_build_keyboard(device_vanilla_build.get('url') if device_vanilla_build is not None else None, device_gapps_build.get('url') if device_gapps_build is not None else None, device_pixelgapps_build.get('url') if device_pixelgapps_build is not None else None, device_foss_build.get('url') if device_foss_build is not None else None, device_codename)
    return device_text, build_keyboard, build_found

# Pyrogram Functions - Commands
@app.on_message(filters=filters.command("start"))
async def start_msg(_: Client, message: Message) -> None:
    if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP] and len(TELEGRAM_GROUP_IDS) > 0 and message.chat.id not in TELEGRAM_GROUP_IDS:
        await message.reply_text("Hey there, this bot cannot be used in this group/supergroup!")
        return
    await message.reply_text(text="Hey there, I'm Bliss Bot!\n\nUse `/help` to check the list of available commands.\nType `/bliss` {codename} to get BlissROMs for your device.", quote=True)

@app.on_message(filters=filters.command("help"))
async def help_msg(_: Client, message: Message) -> None:
    if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP] and len(TELEGRAM_GROUP_IDS) > 0 and message.chat.id not in TELEGRAM_GROUP_IDS:
        await message.reply_text("Hey there, this bot cannot be used in this group/supergroup!")
        return
    await message.reply_text(text="Available commands:\n\n`/bliss` {codename}: Check latest version available for your device.\n`/list`: Check the current list of officially supported devices.", quote=True)

@app.on_message(filters=filters.command("refresh"))
async def refresh_msg(_: Client, message: Message) -> None:
    if message.from_user.id not in AUTHORIZED_IDS:
        await message.reply_text(text="You are not authorized to use this command!", quote=True)
        return
    asyncio.gather(
        download_devices_job(),
        message.reply_text(text="Refreshed devices successfully!", quote=True),
    )

@app.on_message(filters=filters.command("list"))
async def list_msg(_: Client, message: Message) -> None:
    if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP] and len(TELEGRAM_GROUP_IDS) > 0 and message.chat.id not in TELEGRAM_GROUP_IDS:
        await message.reply_text("Hey there, this bot cannot be used in this group/supergroup!")
        return
    devices_list_full = await devices_list()
    list_message = await message.reply_text(text="Please wait, loading the device list...", quote=True)
    text: str = "<strong>Device List:</strong>\n\n"
    if devices_list_full:
        for device, device_data in devices_list_full.items():
            text += f"{html.escape(device_data.get('brand'))} {html.escape(device_data.get('name'))} (<code>{html.escape(device)}</code>)\n"
        await list_message.edit_text(text=text, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]]))
        if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            await asyncio.sleep(10)
            await list_message.delete()
            bot_privileges = (await _.get_chat_member(message.chat.id, (await _.get_me()).id)).privileges
            if bot_privileges and bot_privileges.can_delete_messages:
                await message.delete()
    else:
        await list_message.edit_text(text="Sorry, the device list could not be fetched!")

@app.on_message(filters=filters.command("bliss"))
async def bliss_msg(_: Client, message: Message) -> None:
    if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP] and len(TELEGRAM_GROUP_IDS) > 0 and message.chat.id not in TELEGRAM_GROUP_IDS:
        await message.reply_text("Hey there, this bot cannot be used in this group/supergroup!")
        return
    if len(message.text.split()) < 2 and not message.reply_to_message:
        await message.reply_text(text="Please mention the device codename after `/bliss`. Eg: `/bliss Z01R`", quote=True)
        return
    else:
        devices_list_full = await devices_list()
        if devices_list_full:
            device_codename = message.text.split()[1]
            if device_codename not in devices_list_full.keys():
                await message.reply_text(text="Bliss ROM for the specified device does not exist!\nUse `/list` to check the supported device list", quote=True)
            else:
                await _.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
                device_gapps_build = await get_gapps_build(device_codename=device_codename)
                device_vanilla_build = await get_vanilla_build(device_codename=device_codename)
                device_data = await get_device_info(device_codename=device_codename)
                device_pixelgapps_build = await get_pixelgapps_build(device_codename=device_codename)
                device_foss_build = await get_foss_build(device_codename=device_codename)
                device_text, build_keyboard, build_found = get_device_text(device_vanilla_build=device_vanilla_build, device_gapps_build=device_gapps_build, device_pixelgapps_build=device_pixelgapps_build, device_foss_build=device_foss_build, device_data=device_data, device_codename=device_codename)
                if not build_found:
                    await message.reply_text(text="Bliss ROM for the specified device does not exist!\nUse `/list` to check the supported device list", quote=True)
                else:
                    await message.reply_text(text=device_text, reply_markup=build_keyboard, parse_mode=enums.ParseMode.HTML, quote=True, disable_web_page_preview=True)
        else:
            await message.reply_text(text="Sorry, the device list could not be fetched!", quote=False)

# Pyrogram Functions - Callback Queries
@app.on_callback_query(filters=filters.regex("close"))
async def close_msg(bot: Client, query: CallbackQuery) -> None:
    if query.message.chat.type == enums.ChatType.PRIVATE:
        await query.message.reply_to_message.delete()
    elif query.message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        bot_privileges = (await bot.get_chat_member(query.message.chat.id, (await bot.get_me()).id)).privileges
        if bot_privileges and bot_privileges.can_delete_messages:
            await query.message.reply_to_message.delete()
    await query.message.delete()

scheduler = AsyncIOScheduler()
scheduler.add_job(func=download_devices_job, trigger="interval", hours=3, next_run_time=datetime.datetime.now(), misfire_grace_time=None)

scheduler.start()
app.run()