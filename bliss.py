from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
import json
import httpx
import datetime
import humanfriendly
import html
from typing import Final, Dict, Optional, List
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
AUTHORIZED_IDS: Final[List[int]] = [int(telegram_id) for telegram_id in telegram_config["authorized_ids"]]
DOWNLOAD_BASE_URL: Final[str] = bliss_config["download_url"]

# Pyrogram Client
app = Client("BlissBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Scheduled Jobs
async def download_devices_job() -> None:
    devices_file = "devices.json"
    devices_url = "https://raw.githubusercontent.com/BlissRoms-Devices/official-devices/main/devices.json"
    if os.path.isfile(devices_file):
        new_devices_file = "new_devices.json"
        async with httpx.AsyncClient() as client:
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
        async with httpx.AsyncClient() as client:
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
        devices_url = "https://raw.githubusercontent.com/BlissRoms-Devices/official-devices/main/devices.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(devices_url)
            if response.status_code != 200:
                print(f"Request failed with status code: {response.status_code}")
                return None
            data = json.loads(response.text)
            with open(devices_file, "w") as f:
                json.dump(data, f)
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
    async with httpx.AsyncClient() as client:
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
    async with httpx.AsyncClient() as client:
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
def get_device_keyboard(device_codename: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Vanilla Build", callback_data=f"vanilla#{device_codename}")],
            [InlineKeyboardButton("GApps Build", callback_data=f"gapps#{device_codename}")],
            [InlineKeyboardButton("Close", callback_data="close")],
        ]
    )

def get_build_keyboard(device_codename: str, build_type: str, build_url: str) -> InlineKeyboardMarkup:
    build_keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=f"Download {build_type} ({device_codename})", url=build_url)],
            [InlineKeyboardButton(text="GApps" if build_type == 'Vanilla' else "Vanilla", callback_data=f"gapps#{device_codename}" if build_type == 'Vanilla' else f"vanilla#{device_codename}")],
            [InlineKeyboardButton(text="Back", callback_data=f"back#{device_codename}")],
        ]
    )
    return build_keyboard

def get_device_text(device_data: Optional[Dict[str, str]], device_build: Dict[str, str], build_type: str) -> str:
    if not device_data:
        device_text = ""
    else:
        device_text = f"<strong>Device:</strong> {device_data.get('brand')} {device_data.get('name')}\n<strong>Maintainer:</strong> {device_data.get('maintainer')}\n<strong>Support:</strong> {device_data.get('support')}\n\n"
    device_text += f"<strong>Build Type:</strong> {build_type}\n<strong>Build Date:</strong> {device_build.get('date')}\n<strong>Build Size:</strong> {device_build.get('size')}\n<strong>Build Version:</strong> {device_build.get('version')}"
    return device_text

# Pyrogram Functions - Commands
@app.on_message(filters=filters.command("start"))
async def start_msg(_: Client, message: Message) -> None:
    await message.reply_text(text="Hey there, I'm Bliss Bot!\n\nUse `/help` to check the list of available commands.\nType `/bliss` {codename} to get BlissROMs for your device.", quote=True)

@app.on_message(filters=filters.command("help"))
async def help_msg(_: Client, message: Message) -> None:
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
    devices_list_full = await devices_list()
    list_message = await message.reply_text(text="Please wait, loading the device list...", quote=True)
    text: str = "<strong>Device List:</strong>\n\n"
    if devices_list_full:
        for device, device_data in devices_list_full.items():
            text += f"{html.escape(device_data.get('brand'))} {html.escape(device_data.get('name'))} (<code>{html.escape(device)}</code>)\n"
        await list_message.edit_text(text=text, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]]))
    else:
        await list_message.edit_text(text="Sorry, the device list could not be fetched!")

@app.on_message(filters=filters.command("bliss"))
async def bliss_msg(_: Client, message: Message) -> None:
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
                device_data = devices_list_full.get(device_codename)
                text: str = f"<strong>Device:</strong> {device_data.get('brand')} {device_data.get('name')}\n<strong>Maintainer:</strong> {device_data.get('maintainer')}\n<strong>Support:</strong> {device_data.get('support')}\n\nChoose an option:"
                await message.reply_text(text=text, quote=True, reply_markup=get_device_keyboard(device_codename=device_codename), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
        else:
            await message.reply_text(text="Sorry, the device list could not be fetched!", quote=False)

# Pyrogram Functions - Callback Queries
@app.on_callback_query(filters=filters.regex("close"))
async def close_msg(_: Client, query: CallbackQuery) -> None:
    if query.message.chat.type == enums.ChatType.PRIVATE:
        await query.message.reply_to_message.delete()
    await query.message.delete()

@app.on_callback_query(filters=filters.regex(r'^v\w{6}#\w+$'))
async def vanilla_btn(_: Client, query: CallbackQuery) -> None:
    device_codename = query.data.split('#')[1]
    device_build = await get_vanilla_build(device_codename=device_codename)
    if device_build:
        device_data = await get_device_info(device_codename=device_codename)
        device_text = get_device_text(device_data=device_data, device_build=device_build, build_type="Vanilla")
        await query.edit_message_text(text=device_text, reply_markup=get_build_keyboard(device_codename=device_codename, build_type='Vanilla', build_url=device_build.get('url')), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    else:
        await query.message.edit_text(text=f"Sorry, could not fetch any vanilla build for {device_codename}\nIf you believe this is an error, please report this in our Telegram Chat!")

@app.on_callback_query(filters=filters.regex(r'^g\w{4}#\w+$'))
async def gapps_btn(_: Client, query: CallbackQuery) -> None:
    device_codename = query.data.split('#')[1]
    device_build = await get_gapps_build(device_codename=device_codename)
    if device_build:
        device_data = await get_device_info(device_codename=device_codename)
        device_text = get_device_text(device_data=device_data, device_build=device_build, build_type="GApps")
        await query.edit_message_text(text=device_text, reply_markup=get_build_keyboard(device_codename=device_codename, build_type='GApps', build_url=device_build.get('url')), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    else:
        await query.message.edit_text(text=f"Sorry, could not fetch any vanilla build for {device_codename}\nIf you believe this is an error, please report this in our Telegram Chat!")

@app.on_callback_query(filters=filters.regex(r'^b\w{3}#\w+$'))
async def back_btn(_: Client, query: CallbackQuery) -> None:
    device_codename = query.data.split('#')[1]
    device_data = await get_device_info(device_codename=device_codename)
    if device_data:
        text = f"<strong>Device:</strong> {device_data.get('brand')} {device_data.get('name')}\n<strong>Maintainer:</strong> {device_data.get('maintainer')}\n<strong>Support:</strong> {device_data.get('support')}\n\nChoose an option:"
        await query.edit_message_text(text=text, reply_markup=get_device_keyboard(device_codename=device_codename), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    else:
        await query.message.delete()

scheduler = AsyncIOScheduler()
scheduler.add_job(func=download_devices_job, trigger="interval", hours=3, next_run_time=datetime.datetime.now(), misfire_grace_time=None)

scheduler.start()
app.run()