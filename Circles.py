# ---------------------------------------------------------------------------------
#  /\_/\  🌐 This module was loaded through https://t.me/hikkamods_bot
# ( o.o )  🔓 Not licensed.
#  > ^ <   ⚠️ Owner of heta.hikariatama.ru doesn't take any responsibilities or intellectual property rights regarding this script
# ---------------------------------------------------------------------------------
# Name: Circles
# Description: Округляет всё
# Author: KeyZenD
# Commands:
# .round
# ---------------------------------------------------------------------------------


import io
import logging
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from telethon.tl.types import DocumentAttributeFilename

from .. import loader, utils  # pylint: disable=relative-beyond-top-level

logger = logging.getLogger(__name__)

def register(cb):
    cb(CirclesMod())

@loader.tds
class CirclesMod(loader.Module):
    """округляет всё"""

    strings = {"name": "Circles"}

    def __init__(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self.client = client

    @loader.sudo
    async def roundcmd(self, message):
        """.round <Reply to image/sticker or video/gif>"""
        reply = None
        if message.is_reply:
            reply = await message.get_reply_message()
            data = await check_media(reply)
            if isinstance(data, bool):
                await utils.answer(
                    message, "<b>Reply to image/sticker or video/gif!</b>"
                )
                return
        else:
            await utils.answer(message, "<b>Reply to image/sticker or video/gif!</b>")
            return
        data, media_type = data
        if media_type == "img":
            await message.edit("<b>Processing image</b>📷")
            img = io.BytesIO()
            await message.client.download_file(data, img)
            im = Image.open(img)
            w, h = im.size
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            img.paste(im, (0, 0))
            m = min(w, h)
            img = img.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2))
            w, h = img.size
            mask = Image.new("L", (w, h), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((10, 10, w - 10, h - 10), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(2))
            img = ImageOps.fit(img, (w, h))
            img.putalpha(mask)
            im = io.BytesIO()
            im.name = "img.webp"
            img.save(im)
            im.seek(0)
            await message.client.send_file(message.to_id, im, reply_to=reply)
        else:
            await message.edit("<b>Processing video</b>🎥")
            await message.client.download_file(data, "video.mp4")
            
            # Read video using OpenCV
            cap = cv2.VideoCapture("video.mp4")
            if not cap.isOpened():
                await utils.answer(message, "<b>Failed to open video</b>❌")
                return

            # Get video frame width and height
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            m = min(w, h)
            x_offset = (w - m) // 2
            y_offset = (h - m) // 2

            # Prepare output video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter('result.mp4', fourcc, 30.0, (m, m))

            # Process each frame and crop
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                cropped_frame = frame[y_offset:y_offset + m, x_offset:x_offset + m]
                out.write(cropped_frame)

            # Release resources
            cap.release()
            out.release()

            await message.edit("<b>Saving video</b>📼")
            await message.client.send_file(
                message.to_id, "result.mp4", video_note=True, reply_to=reply
            )
            os.remove("video.mp4")
            os.remove("result.mp4")
        await message.delete()


async def check_media(reply):
    media_type = "img"
    if reply and reply.media:
        if reply.photo:
            data = reply.photo
        elif reply.document:
            if (
                DocumentAttributeFilename(file_name="AnimatedSticker.tgs")
                in reply.media.document.attributes
            ):
                return False
            if reply.gif or reply.video:
                media_type = "vid"
            if reply.audio or reply.voice:
                return False
            data = reply.media.document
        else:
            return False
    else:
        return False
    if not data or data is None:
        return False
    else:
        return (data, media_type)
