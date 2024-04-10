import math
import os

import heroku3
import psutil
import requests
import urllib3
from pyrogram.types import Message

from Hellbot import HEROKU_APP
from Hellbot.core.config import all_env, os_configs
from Hellbot.functions.paste import spaceBin
from Hellbot.functions.templates import usage_templates
from Hellbot.functions.tools import restart, update_dotenv

from . import Config, HelpMenu, Symbols, db, hellbot, on_message

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Heroku = heroku3.from_key(Config.HEROKU_APIKEY)


@on_message("getvar", allow_stan=True)
async def getvar(_, message: Message):
    if len(message.command) < 2:
        return await hellbot.delete(message, "Give a varname to fetch value.")

    varname = message.command[1]
    if varname.upper() in os_configs:
        value = os.environ.get(varname.upper(), None)
    else:
        value = await db.get_env(varname.upper())

    if isinstance(value, str):
        await hellbot.edit(
            message,
            f"{Symbols.anchor} **Variable Name:** `{varname.upper()}`\n{Symbols.anchor} **Value:** `{value}`",
        )
    elif value is None:
        await hellbot.delete(message, f"**Variable {varname} does not exists!**")


@on_message(["getallvar", "getallvars"], allow_stan=True)
async def getallvar(_, message: Message):
    text = "**📃 List of all variable are:**\n\n"
    for env in all_env:
        text += f"   {Symbols.anchor} `{env}`\n"

    for config in os_configs:
        text += f"   {Symbols.anchor} `{config}`\n"

    await hellbot.edit(message, text)


@on_message("setvar", allow_stan=True)
async def setvar(_, message: Message):
    if len(message.command) < 3:
        return await hellbot.delete(
            message, "**Give varname and var-value along with the command!**"
        )

    is_heroku = False
    input_str = (await hellbot.input(message)).split(" ", 1)
    varname = input_str[0]
    varvalue = input_str[1]

    if varname.upper() in os_configs:
        if HEROKU_APP:
            try:
                app = Heroku.app(Config.HEROKU_APPNAME)
                config = app.config()
                oldValue = (
                    config[varname.upper()] if varname.upper() in config else "None"
                )
                is_heroku = True
            except BaseException:
                return await hellbot.error(
                    message, "`HEROKU_APIKEY` or `HEROKU_APPNAME` is Invalid!"
                )
        else:
            oldValue = os.environ.get(varname.upper(), "None")
            await update_dotenv(varname.upper(), varvalue)

        await hellbot.edit(
            message,
            f"**{Symbols.anchor} Variable:** `{varname.upper()}` \n\n"
            f"**{Symbols.anchor} Old Value:** `{oldValue}` \n\n"
            f"**{Symbols.anchor} New Value:** `{varvalue}`\n\n"
            "__Restarting to apply changes!__",
        )

        if is_heroku:
            config[varname.upper()] = varvalue

        return await restart()

    oldValue = await db.get_env(varname.upper())
    await db.set_env(varname.upper(), varvalue)
    await hellbot.delete(
        message,
        f"**{Symbols.anchor} Variable:** `{varname.upper()}` \n\n"
        f"**{Symbols.anchor} Old Value:** `{oldValue}` \n\n"
        f"**{Symbols.anchor} New Value:** `{varvalue}`",
    )


@on_message("delvar", allow_stan=True)
async def delvar(_, message: Message):
    if len(message.command) < 2:
        return await hellbot.delete(message, "**Give varname along with the command!**")

    varname = message.command[1]
    if varname.upper() in os_configs:
        return await hellbot.error(
            message, "You can't delete this var for security reasons."
        )

    if await db.is_env(varname.upper()):
        await db.rm_env(varname.upper())
        await hellbot.delete(
            message, f"**Variable** `{varname.upper()}` **deleted successfully!**"
        )
        return

    await hellbot.delete(message, "**No such variable found in database to delete!**")


@on_message("usage", allow_stan=True)
async def dynoUsage(_, message: Message):
    hell = await hellbot.edit(message, "Fetching usage info...")

    percentage = 0
    hours = 0
    minutes = 0
    appHours = 0
    appMinutes = 0
    appPercentage = 0

    if HEROKU_APP:
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36",
            "Authorization": f"Bearer {Config.HEROKU_APIKEY}",
            "Accept": "application/vnd.heroku+json; version=3.account-quotas",
        }
        herokuId = Heroku.account().id
        apiUrl = f"https://api.heroku.com/accounts/{herokuId}/actions/get-quota"

        response = requests.get(apiUrl, headers=HEADERS)
        if response.status_code != 200:
            return await hellbot.error(message, "Something went wrong!")

        result: dict = response.json()

        herokuApp = result.get("apps", {})
        quota = result.get("account_quota", 0)
        quotaUsed = result.get("quota_used", 0)
        quotaRemaining = quota - quotaUsed
        minutesRemaining = quotaRemaining / 60
        percentage = math.floor(quotaRemaining / quota * 100)
        hours = math.floor(minutesRemaining / 60)
        minutes = math.floor(minutesRemaining % 60)

        try:
            herokuApp[0]["quota_used"]
        except IndexError:
            appQuotaUsed = 0
            appPercentage = 0
        else:
            appQuotaUsed = herokuApp[0]["quota_used"] / 60
            appPercentage = math.floor(herokuApp[0]["quota_used"] / quota * 100)

        appHours = math.floor(appQuotaUsed / 60)
        appMinutes = math.floor(appQuotaUsed % 60)

    try:
        disk = psutil.disk_usage("/")
        diskTotal = int(disk.total / (1024.0**3))
        diskUsed = int(disk.used / (1024.0**3))
        diskPercent = disk.percent
    except:
        diskTotal = 0
        diskUsed = 0
        diskPercent = 0

    try:
        memory = psutil.virtual_memory()
        memoryTotal = int(memory.total / (1024.0**3))
        memoryUsed = int(memory.used / (1024.0**3))
        memoryPercent = memory.percent
    except:
        memoryTotal = 0
        memoryUsed = 0
        memoryPercent = 0

    await hell.edit(
        await usage_templates(
            appName=Config.HEROKU_APPNAME,
            appHours=appHours,
            appMinutes=appMinutes,
            appPercentage=appPercentage,
            hours=hours,
            minutes=minutes,
            percentage=percentage,
            diskUsed=diskUsed,
            diskTotal=diskTotal,
            diskPercent=diskPercent,
            memoryUsed=memoryUsed,
            memoryTotal=memoryTotal,
            memoryPercent=memoryPercent,
        )
    )


@on_message("logs", allow_stan=True)
async def getLogs(_, message: Message):
    limit = int(message.command[1]) if len(message.command) > 1 else 100

    try:
        if os.path.exists("HellBot.log"):
            with open("HellBot.log", "r") as file:
                logData = file.readlines()
                logData = "".join(logData[-limit:])
            file.close()

            with open("log.txt", "w") as file:
                file.write(logData)
            file.close()

            link = spaceBin(logData)
            await message.reply_document(
                "log.txt",
                caption=f"**Link to logs:** [click here]({link})",
                file_name="log.txt",
            )
            os.remove("log.txt")
    except Exception as e:
        await hellbot.error(message, str(e))


HelpMenu("manager").add(
    "getvar",
    "<varname>",
    "Get value of a varname from env or database.",
    "getvar handler",
).add(
    "getallvar",
    None,
    "Get the name of every env and database variable.",
).add(
    "setvar",
    "<varname> <value>",
    "Set value of a varname to env or database.",
    "setvar handler !",
).add(
    "delvar", "<varname>", "Delete a varname from env or database.", "delvar handler"
).add(
    "usage",
    None,
    "Get dyno, disk and RAM usage of your bot server.",
    "usage",
    "Dyno usage is only available for heroku users.",
).add(
    "logs",
    "<limit>",
    "Get last 'n' lines of log file. By default limit is 100 lines if not mentioned with the command",
    "logs 69",
).info(
    "Manage your bot with ease!"
).done()
