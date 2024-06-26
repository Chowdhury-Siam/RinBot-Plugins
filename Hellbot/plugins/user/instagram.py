import os
import re
import time

import requests
from pyrogram.types import Message
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, visibility_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from Hellbot.functions.driver import Driver
from Hellbot import LOGS

from . import HelpMenu, hellbot, on_message


def obtain_ids(user: str):
    response = requests.get("https://www.instagram.com/" + user)
    appid = re.search(r'appId":"(\d*)', response.text)[1]
    serverid = re.search(r'server_revision":(\d*)', response.text)[1]

    return appid, serverid


@on_message("reels", allow_stan=True)
async def instagramReels(_, message: Message):
    if len(message.command) < 2:
        return await hellbot.delete(
            message, "Give an instagram reels link to download."
        )

    hell = await hellbot.edit(message, "Searching...")

    query = await hellbot.input(message)
    isInstagramLink = lambda link: bool(
        (re.compile(r"^https?://(?:www\.)?instagram\.com/reel/")).match(link)
    )

    if not isInstagramLink(query):
        return await hellbot.error(hell, "Give a valid instagram reels link.")

    try:
        driver, _ = Driver.get()
        if not driver:
            return await hellbot.error(hell, _)

        driver.get(query)
        wait = WebDriverWait(driver, 10)
        element = wait.until(presence_of_element_located((By.TAG_NAME, "video")))
        reels = element.get_attribute("src")
        driver.quit()

        if reels:
            await hell.edit("Found the reel. **Downloading...**")

            binary = requests.get(reels).content
            fileName = f"reels_{int(time.time())}.mp4"
            with open(fileName, "wb") as file:
                file.write(binary)

            await hell.edit("Uploading...")
            await message.reply_video(
                fileName,
                caption=f"__💫 Downloaded Instagram Reels!__ \n\n**</> @HellBot_Networks**",
            )
            await hell.delete()
            os.remove(fileName)
        else:
            await hellbot.error(
                hell,
                "Unable to download the reel. Make sure the link is valid or the reel is not from a private account.",
            )
    except Exception as e:
        await hellbot.error(hell, f"**Error:** `{e}`")


# @on_message("igpost", allow_stan=True)
# async def instagramPosts(_, message: Message):
#     if len(message.command) < 2:
#         return await hellbot.delete(
#             message, "Give an instagram post link to download."
#         )

#     hell = await hellbot.edit(message, "Searching...")

#     query = await hellbot.input(message)
#     isInstagramLink = lambda link: bool(
#         (re.compile(r"^https?://(?:www\.)?instagram\.com/p/")).match(link)
#     )

#     if not isInstagramLink(query):
#         return await hellbot.error(hell, "Give a valid instagram post link.")

#     try:
#         driver, _ = Driver.get()
#         if not driver:
#             return await hellbot.error(hell, _)

#         driver.get(query)
#         wait = WebDriverWait(driver, 10)

#         try:    
#             element = wait.until(presence_of_element_located((By.TAG_NAME, "video")))
#             extention = "mp4"
#         except:
#             element = wait.until(presence_of_element_located((By.TAG_NAME, "img")))
#             extention = "jpg"

#         media = element.get_attribute("src")
#         driver.quit()
#         if media:
#             await hell.edit("Found the post. **Downloading...**")

#             binary = requests.get(media).content
#             fileName = f"media_{int(time.time())}.{extention}"
#             with open(fileName, "wb") as file:
#                 file.write(binary)

#             await hell.edit("Uploading...")
#             await message.reply_document(
#                 fileName,
#                 caption=f"__💫 Downloaded Instagram Post!__ \n\n**</> @HellBot_Networks**",
#                 force_document=False,
#             )
#             await hell.delete()
#             os.remove(fileName)
#         else:
#             await hellbot.error(
#                 hell,
#                 "Unable to download the post. Make sure the link is valid or the post is not from a private account.",
#             )
#     except Exception as e:
#         await hellbot.error(hell, f"**Error:** `{e}`")


@on_message("igpost", allow_stan=True)
async def instagramPost(_, message: Message):
    if len(message.command) < 2:
        return await hellbot.delete(message, "Give an instagram post link to download.")

    hell = await hellbot.edit(message, "Searching...")

    query = await hellbot.input(message)
    isInstagramLink = lambda link: bool(
        (re.compile(r"^https?://(?:www\.)?instagram\.com/p/")).match(link)
    )

    if not isInstagramLink(query):
        return await hellbot.error(hell, "Give a valid instagram post link.")

    try:
        driver, _ = Driver.get()
        if not driver:
            return await hellbot.error(hell, _)

        media = []
        driver.get(query)
        wait = WebDriverWait(driver, 10)

        # get the first media
        try:
            element = wait.until(visibility_of_element_located((By.TAG_NAME, "video")))
            extention = "mp4"
        except:
            element = wait.until(visibility_of_element_located((By.TAG_NAME, "img")))
            extention = "jpg"
        media.append((element.get_attribute("src"), extention))

        # check if there are more media
        try:
            button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
        except:
            button = False

        # get all media
        while button:
            try:
                button.click()
                try:
                    element = wait.until(visibility_of_element_located((By.TAG_NAME, "video")))
                    extention = "mp4"
                except:
                    element = wait.until(visibility_of_element_located((By.TAG_NAME, "img")))
                    extention = "jpg"
                media.append((element.get_attribute("src"), extention))
                try:
                    button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                except:
                    button = False
            except Exception as e:
                LOGS.info("--> " + str(e))

        driver.quit()

        if media:
            await hell.edit("**Downloading...**")

            for post in media:
                binary = requests.get(post[0]).content
                fileName = f"post_{int(time.time())}.{post[1]}"
                with open(fileName, "wb") as file:
                    file.write(binary)
                await message.reply_document(
                    fileName,
                    caption=f"__💫 Downloaded Instagram Post!__ \n\n**</> @Chowdhury_Siam**",
                    force_document=False,
                )
                await hell.delete()
                os.remove(fileName)
        else:
            await hellbot.error(
                hell,
                "Unable to download the post. Make sure the link is valid or the post is not from a private account.",
            )
    except Exception as e:
        await hellbot.error(hell, f"`{e}`")


@on_message("iguser", allow_stan=True)
async def instagramUser(_, message: Message):
    if len(message.command) < 2:
        return await hellbot.delete(message, "Give an instagram username to fetch info.")

    BASE_URL = "https://i.instagram.com/api/v1/users/web_profile_info/"

    query = (await hellbot.input(message)).replace("@", "").strip()
    hell = await hellbot.edit(message, f"**Searching** `{query}` **on instagram**...")

    appid, serverid = obtain_ids(query)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) 20100101 Firefox/103.0",
        "Accept": "*/*",
        "Accept-Language": "en,en-US;q=0.3",
        "X-Instagram-AJAX": serverid,
        "X-IG-App-ID": appid,
        "X-ASBD-ID": "198337",
        "X-IG-WWW-Claim": "0",
        "Origin": "https://www.instagram.com",
        "DNT": "1",
        "Alt-Used": "i.instagram.com",
        "Connection": "keep-alive",
        "Referer": "https://www.instagram.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
    }

    params = {"username": query}

    try:
        response: dict = requests.get(BASE_URL, params, headers=headers).json()

        if response["status"] != "ok":
            return await hellbot.error(
                hell,
                f"**Message:** `{response['message']}`\n**Required Login:** `{response['require_login']}`"
            )

        data = response["data"]["user"]
        about = data["biography"] if data["biography"] else "Not Available"
        followers = data["edge_followed_by"]["count"]
        following = data["edge_follow"]["count"]
        full_name = data["full_name"]
        is_private = data["is_private"]
        is_verified = data["is_verified"]
        posts = data["edge_owner_to_timeline_media"]["count"]
        username = data["username"]

        profile_pic = f"iguser_{int(time.time())}.jpg"
        with open(profile_pic, "wb") as f:
            f.write(requests.get(data["profile_pic_url_hd"]).content)

        await message.reply_photo(
            profile_pic,
            caption=(
                f"**🍀 Full Name:** `{full_name}`\n"
                f"**👤 Username:** [{username}](https://instagram.com/{username})\n"
                f"**👁‍🗨 Private:** `{is_private}`\n"
                f"**👑 Verified:** `{is_verified}`\n"
                f"**📸 Posts:** `{posts}`\n"
                f"**💫 Followers:** `{followers}`\n"
                f"**🍂 Following:** `{following}`\n"
                f"**💬 Bio:** `{about}`\n\n"
                "**</> @Chowdhury_Siam**"
            ),
        )
        await hell.delete()
        os.remove(profile_pic)
    except Exception as e:
        return await hellbot.error(hell, f"`{e}`")


HelpMenu("instagram").add(
    "reels",
    "<instagram reels link>",
    "Download instagram reels.",
    "reels https://www.instagram.com/reel/Cr24EiKNTL7/",
).add(
    "igpost",
    "<instagram post link>",
    "Download instagram post.",
    "igpost https://www.instagram.com/p/C06rAjDJlJs/",
    "If the post has multiple videos, it will download all of them one by one.",
).add(
    "iguser",
    "<instagram username>",
    "Get instagram user info.",
    "iguser therock",
).info(
    "Instagram Scrapper"
).done()
