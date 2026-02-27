# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | TG-SORRY

import os
import time
import random
import logging
import re
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import requests
import urllib.parse
import filetype
import shutil
import tldextract
import asyncio
import json
import math
from urllib.parse import urlparse, unquote
from PIL import Image
from plugins.config import Config
from plugins.script import Translation
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram import filters
from pyrogram import enums
from pyrogram import Client
from plugins.peerfix import ensure_peer
from plugins.functions.verify import verify_user, check_token, check_verification, get_token
from plugins.functions.forcesub import handle_force_subscribe
from plugins.functions.display_progress import humanbytes
from plugins.functions.help_uploadbot import DownLoadFile
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from plugins.functions.ran_text import random_char
from plugins.database.database import db
from plugins.database.add import AddUser
from pyrogram.types import Thumbnail
cookies_file = 'cookies.txt'


def get_filename_from_url_sync(url):
    """
    Get the real filename from URL by checking Content-Disposition header.
    Falls back to URL basename if no Content-Disposition header is found.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=30)

        # Check Content-Disposition header for filename
        content_disposition = response.headers.get('Content-Disposition', '')
        if content_disposition:
            # Try to extract filename from Content-Disposition
            # Format: attachment; filename="filename.mkv" or attachment; filename*=UTF-8''filename.mkv
            filename_match = re.findall(r"filename[*]?=[\"']?(?:UTF-8'')?([^\"';]+)[\"']?", content_disposition)
            if filename_match:
                filename = filename_match[-1].strip()
                # URL decode the filename
                filename = unquote(filename)
                # Remove any path components, keep only the filename
                filename = os.path.basename(filename)
                if filename:
                    logger.info(f"Found filename from Content-Disposition: {filename}")
                    return filename

        # Fallback: try to get filename from final URL
        parsed_url = urlparse(response.url)
        url_filename = os.path.basename(unquote(parsed_url.path))
        if url_filename and '.' in url_filename:
            logger.info(f"Using filename from URL: {url_filename}")
            return url_filename

    except Exception as e:
        logger.warning(f"Error getting filename from headers: {e}")

    # Final fallback: use URL basename
    try:
        parsed_url = urlparse(url)
        return os.path.basename(unquote(parsed_url.path)) or "unknown_file"
    except:
        return "unknown_file"


@Client.on_message(filters.private & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    if update.from_user.id != Config.OWNER_ID:
        if not await check_verification(bot, update.from_user.id) and Config.TRUE_OR_FALSE:
            button = [[
                InlineKeyboardButton("✓⃝ Vᴇʀɪꜰʏ ✓⃝", url=await get_token(bot, update.from_user.id, f"https://telegram.me/{Config.BOT_USERNAME}?start="))
                ],[
                InlineKeyboardButton("🔆 Wᴀᴛᴄʜ Hᴏᴡ Tᴏ Vᴇʀɪꜰʏ 🔆", url=f"{Config.VERIFICATION}")
            ]]
            await update.reply_text(
                text="<b>Pʟᴇᴀsᴇ Vᴇʀɪꜰʏ Fɪʀsᴛ Tᴏ Usᴇ Mᴇ</b>",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup(button)
            )
            return
    if Config.LOG_CHANNEL:
        try:
            await ensure_peer(bot, Config.LOG_CHANNEL)
            log_message = await update.forward(Config.LOG_CHANNEL)
            log_info = "Message Sender Information\n"
            log_info += "\nFirst Name: " + update.from_user.first_name
            log_info += "\nUser ID: " + str(update.from_user.id)
            log_info += "\nUsername: @" + (update.from_user.username if update.from_user.username else "")
            log_info += "\nUser Link: " + update.from_user.mention
            await log_message.reply_text(
                text=log_info,
                disable_web_page_preview=True,
                quote=True
            )
        except Exception as error:
            print(error)
    if not update.from_user:
        return await update.reply_text("I don't know about you sar :(")
    await AddUser(bot, update)
    if Config.UPDATES_CHANNEL:
        fsub = await handle_force_subscribe(bot, update)
        if fsub == 400:
            return


    logger.info(update.from_user)
    url = update.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None

    print(url)
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0]
            file_name = url_parts[1]
        elif len(url_parts) == 4:
            url = url_parts[0]
            file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(url)
        logger.info(file_name)
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]

    use_cookies = os.path.exists(cookies_file)
    if Config.HTTP_PROXY != "":
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--allow-dynamic-mpd",
            "--no-check-certificate",
            "-j",
            url,
            "--proxy", Config.HTTP_PROXY
        ]
    else:
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--allow-dynamic-mpd",
            "--no-check-certificate",
            "-j",
            url,
            "--geo-bypass-country",
            "IN"

        ]
    if use_cookies:
        command_to_exec.extend(["--cookies", cookies_file])
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    logger.info(command_to_exec)
    chk = await bot.send_message(
            chat_id=update.chat.id,
            text=f'Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ ⌛',
            disable_web_page_preview=True,
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML
          )
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    logger.info(e_response)
    t_response = stdout.decode().strip()
    if e_response and "nonnumeric port" not in e_response:
        # logger.warn("Status : FAIL", exc.returncode, exc.output)
        error_message = e_response.replace("please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", "")
        if "This video is only available for registered users." in error_message:
            error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
        await chk.delete()

        time.sleep(10)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            reply_to_message_id=update.id,
            disable_web_page_preview=True
        )
        return False
    if t_response:
        x_reponse = t_response
        if "\n" in x_reponse:
            x_reponse, _ = x_reponse.split("\n")
        response_json = json.loads(x_reponse)
        randem = random_char(5)
        save_ytdl_json_path = Config.DOWNLOAD_LOCATION +             "/" + str(update.from_user.id) + f'{randem}' + ".json"
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        # Skip format selection - use user settings directly
        await chk.delete()

        # Get user's upload preference from settings
        upload_as_doc = await db.get_upload_as_doc(update.from_user.id)

        # Select best format automatically (highest quality with reasonable size)
        best_format = None
        best_size = 0
        if "formats" in response_json:
            for fmt in response_json["formats"]:
                format_id = fmt.get("format_id")
                format_ext = fmt.get("ext", "mp4")
                if fmt.get('filesize'):
                    size = fmt['filesize']
                elif fmt.get('filesize_approx'):
                    size = fmt['filesize_approx']
                else:
                    size = 0
                # Skip audio-only formats for auto-selection
                format_note = fmt.get("format_note") or fmt.get("format") or ""
                if "audio only" in format_note.lower():
                    continue
                # Select format with best quality (largest size but under 2GB)
                if size > best_size and size < 2147483648:  # 2GB limit
                    best_size = size
                    best_format = fmt

        # If no suitable format found, use the default
        if not best_format and "formats" in response_json and len(response_json["formats"]) > 0:
            # Find first non-audio format
            for fmt in response_json["formats"]:
                format_note = fmt.get("format_note") or fmt.get("format") or ""
                if "audio only" not in format_note.lower():
                    best_format = fmt
                    break
            if not best_format:
                best_format = response_json["formats"][-1]  # Use last format as fallback

        if best_format:
            format_id = best_format.get("format_id")
            format_ext = best_format.get("ext", "mp4")
        else:
            format_id = response_json.get("format_id", "best")
            format_ext = response_json.get("ext", "mp4")

        # Determine send type based on user settings
        # upload_as_doc=True means upload as VIDEO (reply_video)
        # upload_as_doc=False means upload as DOCUMENT (reply_document)
        if upload_as_doc:
            tg_send_type = "video"
        else:
            tg_send_type = "file"

        # Create callback data and trigger download directly
        cb_data = f"{tg_send_type}|{format_id}|{format_ext}|{randem}"

        # Send a new message for download progress
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        import time
        cancel_id = f"{update.from_user.id}_{int(time.time())}"
        cancel_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⛔ Cancel", callback_data=f"cancel_ytdl_{cancel_id}")]
        ])

        title = response_json.get('title', 'Unknown')
        progress_msg = await bot.send_message(
            chat_id=update.chat.id,
            text=f"📥 <b>Starting Download...</b>\n\n<b>Title:</b> <code>{title}</code>",
            reply_markup=cancel_markup,
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML
        )

        # Create a mock update object for the callback
        class MockMessage:
            def __init__(self, msg, chat_id, msg_id):
                self.message_id = msg_id
                self.chat = type('obj', (object,), {'id': chat_id})()
                self._msg = msg

            async def edit_caption(self, **kwargs):
                await self._msg.edit_text(**kwargs)

            async def reply_document(self, **kwargs):
                return await self._msg.reply_document(**kwargs)

            async def reply_video(self, **kwargs):
                return await self._msg.reply_video(**kwargs)

            async def reply_audio(self, **kwargs):
                return await self._msg.reply_audio(**kwargs)

            async def reply_video_note(self, **kwargs):
                return await self._msg.reply_video_note(**kwargs)

        class MockCallback:
            def __init__(self, data, message, from_user, reply_to_msg):
                self.data = data
                self.message = message
                self.from_user = from_user
                self.reply_to_message = reply_to_msg

        mock_msg = MockMessage(progress_msg, update.chat.id, progress_msg.id)
        mock_update = MockCallback(cb_data, mock_msg, update.from_user, update)

        # Import and call the youtube_dl callback directly
        from plugins.button import youtube_dl_call_back
        await youtube_dl_call_back(bot, mock_update)

    else:
        # Fallback for non-yt-dlp links (direct download links)
        # Get the real filename from the URL
        detected_filename = get_filename_from_url_sync(url)

        await chk.delete()

        # Get user's upload preference from settings
        upload_as_doc = await db.get_upload_as_doc(update.from_user.id)

        # Determine send type based on user settings
        # upload_as_doc=True means upload as VIDEO (reply_video)
        # upload_as_doc=False means upload as DOCUMENT (reply_document)
        if upload_as_doc:
            tg_send_type = "video"
            youtube_dl_format = "OFL"
            youtube_dl_ext = "ENON"
        else:
            tg_send_type = "file"
            youtube_dl_format = "LFO"
            youtube_dl_ext = "NONE"

        # Create callback data for direct download
        cb_data = f"{tg_send_type}={youtube_dl_format}={youtube_dl_ext}"

        # Send a new message for download progress
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        import time
        cancel_id = f"{update.from_user.id}_{int(time.time())}"
        cancel_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⛔ Cancel", callback_data=f"cancel_dl_{cancel_id}")]
        ])

        progress_msg = await bot.send_message(
            chat_id=update.chat.id,
            text=f"📥 <b>Starting Download...</b>\n\n<b>File:</b> <code>{detected_filename}</code>",
            reply_markup=cancel_markup,
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML
        )

        # Create a mock update object for the callback
        class MockMessage:
            def __init__(self, msg, chat_id, msg_id):
                self.message_id = msg_id
                self.chat = type('obj', (object,), {'id': chat_id})()
                self._msg = msg

            async def edit_caption(self, **kwargs):
                await self._msg.edit_text(**kwargs)

            async def reply_document(self, **kwargs):
                return await self._msg.reply_document(**kwargs)

            async def reply_video(self, **kwargs):
                return await self._msg.reply_video(**kwargs)

            async def reply_audio(self, **kwargs):
                return await self._msg.reply_audio(**kwargs)

            async def reply_video_note(self, **kwargs):
                return await self._msg.reply_video_note(**kwargs)

        class MockCallback:
            def __init__(self, data, message, from_user, reply_to_msg):
                self.data = data
                self.message = message
                self.from_user = from_user
                self.reply_to_message = reply_to_msg

        mock_msg = MockMessage(progress_msg, update.chat.id, progress_msg.id)
        mock_update = MockCallback(cb_data, mock_msg, update.from_user, update)

        # Import and call the ddl callback directly
        from plugins.dl_button import ddl_call_back
        await ddl_call_back(bot, mock_update)
