import requests
import time
import os
from pyrogram import filters
from . import HelpMenu, hellbot, on_message


@on_message("gen", allow_stan=True)
async def generate_image(client, message):
   
    prompt = ' '.join(message.command[1:])

    text = await message.reply_text("Please wait while I generate the image...")
    StartTime = time.time()


    # API endpoint URL
    url = 'https://ai-api.magicstudio.com/api/ai-art-generator'

    # Form data for the request
    form_data = {
        'prompt': prompt,
        'output_format': 'bytes',
        'request_timestamp': str(int(time.time())),
        'user_is_subscribed': 'false',
    }

    # Send a POST request to the API
    response = requests.post(url, data=form_data)

    if response.status_code == 200:
        try:
            if response.content:
                destination_dir = ''
                destination_path = os.path.join(destination_dir, 'Siam_Ai_Generated_image.jpg')

                # Save the image to the destination path
                with open(destination_path, 'wb') as f:
                    f.write(response.content)

                # Delete the wait message
                await text.delete()

                # Send the generated image
                await message.reply_photo(destination_path, caption=f"Here's the generated image!\nTime Taken: {time.time() - StartTime}\n\nGenerated by @Chowdhury_Siam")

                # Delete the generated image after sending
                os.remove(destination_path)
            else:
                await text.edit_text("Failed to generate the image.")
        except Exception as e:
            await text.edit_text("Error: {}".format(e))
    else:
        await text.edit_text("Error: {}".format(response.status_code))

    HelpMenu("ai").add(
    "gen",
    "<query>",
    "Generate Ai image from https://ai-api.magicstudio.com,",
    "gen Miku Nakano",
).info(
    "Image Tools"
).done()
