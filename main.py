import os
import re
import random
import asyncio
import discord
import yt_dlp
from rs import get_happening, get_yle_news, get_yle_latest_news
from constants import DISCORD_TOKEN, MY_ID, YLE_BOTTI_CHANNELS
from weather import get_weather
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

playlist = []

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    asyncio.create_task(yle_latest_news_polling())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f'Message content: {message.content}')

    try:
        command = message.content.split()[0]
    except IndexError as e:
        print(f'Error: {e}')
        return

    if (command[0] != '!'):
        print("\tNot a command")
        return

    if (command == '!join'): 
        await join_voice_channel(message)
    elif (command == '!leave'):
        await leave_voice_channel(message)
    elif (command == '!yt'):
        await play_youtube(message)
    elif (command == '!rm'):
        await delete_from_playlist(message)
    elif (command == '!playlist'):
        await print_playlist(message)
    elif (command == '!skip'):
        await skip(message)
    elif (command == '!delete'):
        await delete(message)
    elif (command == '!häppening'):
        await happening(message)
    elif (command == '!yle'):
        await yle_news(message)
    elif (command == '!kainuu'):
        await yle_news(message)
    elif (command == '!commands'):
        await print_commands(message)
    elif (command == '!weather' or command == '!w'):
        await weather(message)
    elif (command == '!licenses'):
        await licenses(message)
    else: print('Unknown command')

async def weather(message):
    parts = message.content.split()
    if len(parts) == 2:
        city = parts[1]
    elif len(parts) >= 3:
        print(parts[2])
        await message.channel.send(content=await get_weather('kajaani', parts[2]))
        return
    else:
        await message.channel.send(content=await get_weather('kajaani'))
        return

    await message.channel.send(content=await get_weather(city))

@client.event
async def happening(message):
    await message.channel.send(content=await get_happening())

@client.event
async def yle_news(message):
    if (message.content == '!yle'):
        res = await get_yle_news('major')
    elif (message.content == '!kainuu'):
        res = await get_yle_news('kainuu')

    await message.channel.send(content=res)

@client.event
async def yle_latest_news_polling():
    while True:
        try:
            news = await get_yle_latest_news()
            if news:
                for i in YLE_BOTTI_CHANNELS:
                    channel = client.get_channel(i)
                    if channel:
                        await channel.send(news, allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            print(f"Error occurred while polling YLE latest news RSS feed: {e}.")

        await asyncio.sleep(360)

@client.event
async def join_voice_channel(message):
    if not message.author.voice:
        await message.channel.send(f"{message.author.name} is not connected to a voice channel")
        return

    channel = message.author.voice.channel
    await channel.connect()

@client.event
async def leave_voice_channel(message):
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()

@client.event
async def play_youtube(message):
    if not message.guild.voice_client:
        await join_voice_channel(message)

    parts = message.content.split()
    if len(parts) >= 2:
        url = parts[1]
    else:
        await message.channel.send("Usage: !yt <url>")
        return

    ydl_options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': './audio/%(title)s.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        downloaded_file = os.path.join("audio", f"{info_dict['title']}.mp3")

        if not os.path.exists(downloaded_file):
            ydl.download([url])

        playlist.append(f"{info_dict['title']}")

    if message.guild.voice_client.is_playing():
        return
    
    async def play_next_song():
        while playlist:
            try:
                source = discord.FFmpegPCMAudio(f'audio/{playlist[0]}.mp3')
                message.guild.voice_client.play(source)
                while message.guild.voice_client.is_playing():
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"An error occurred while playing the audio: {e}")

            playlist.pop(0)

        folder_path = './audio'
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file: {file_path}, Error: {e}")

    await play_next_song()

@client.event
async def print_playlist(message):
    playlist_message = ''
    i = 1
    for song in playlist:
        playlist_message += f"{i}. {song}\n"
        i += 1

    await message.channel.send(content=playlist_message)

@client.event
async def delete_from_playlist(message):
    parts = message.content.split()
    if len(parts) >= 2:
        index = parts[1]
    else:
        await message.channel.send("Usage: !rm <index>")
        return
    try:
        index = int(index)
        if 1 <= index <= len(playlist):
            removed_song = playlist.pop(index - 1)
            await message.channel.send(f"Removed song '{removed_song}' from playlist.")
            await print_playlist(message)
        else:
            await message.channel.send("Invalid index. Please provide a valid index from the playlist.")
            await print_playlist(message)
    except ValueError:
        await message.channel.send("Invalid index. Please provide a valid integer index from the playlist.")

@client.event
async def skip(message):
    if message.guild.voice_client and message.guild.voice_client.is_playing():
        message.guild.voice_client.stop()
        await message.channel.send("Skipping the current song.")
    else:
        await message.channel.send("No song is currently playing.")

@client.event
async def delete(message):
    if message.content.startswith('!delete'):
        parts = message.content.split()
        if len(parts) >= 3:
            try:
                num_messages = int(parts[1])
                match = re.search(r'\d+', parts[2])
                if match:
                    user_id = int(match.group())
                if message.channel.permissions_for(message.guild.me).manage_messages:
                    deleted = await message.channel.purge(limit=num_messages + 1, check=lambda m: m.author.id == user_id)
                    confirmation_message = await message.channel.send(f"Deleted {len(deleted) - 1} message(s) from <@{user_id}>.")

                    await asyncio.sleep(3)
                    await confirmation_message.delete()
                else:
                    await message.channel.send("I don't have permission to manage messages.")
            except (ValueError, IndexError):
                await message.channel.send("Invalid parameters. Please specify the number of messages to delete and the user.")
        elif len(parts) >= 2:
            try:
                num_messages = int(parts[1])
                if message.channel.permissions_for(message.guild.me).manage_messages:
                    deleted = await message.channel.purge(limit=num_messages + 1)
                    confirmation_message = await message.channel.send(f"Deleted {len(deleted) - 1} message(s).")

                    await asyncio.sleep(3)
                    await confirmation_message.delete()
                else:
                    await message.channel.send("I don't have permission to manage messages.")
            except (ValueError, IndexError):
                await message.channel.send("Invalid parameters. Please specify the number of messages to delete.")
        else:
            await message.channel.send("Usage: !delete <number_of_messages> <@user> or !delete <number_of_messages>")

async def rand_image(folder):

    image_files = os.listdir(folder)
    random_image = random.choice(image_files)

    image_path = os.path.join(folder, random_image)

    return image_path

@client.event
async def print_commands(message):
    res = '''```md
!join      - Joins to a voice channel
!leave     - Leaves a voice channel
!yt        - Play audio from Youtube | !yt <url>
!skip      - Skips current song
!delete    - Deletes messages | !delete <number_of_messages> <@user> or !delete <number_of_messages>
!häppening - Retrieves latest häppenings from Pelastustoimen mediapalvelu
!yle       - Retrieves Major Headlines from Yle
!weather   - Weather forecast | !sää <city>
!licenses  - Sends licenses file
```'''
    await message.channel.send(content=res)

async def licenses(message):
    with open('licenses.md', 'rb') as file:
        await message.channel.send(file=discord.File(file, 'licenses.md'))

client.run(DISCORD_TOKEN)