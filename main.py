# discord modules
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
# yt modules
from youtubesearchpython.__future__ import VideosSearch # async version of the library
import pafy
# other
from collections import deque
import asyncio


class Video:
    def __init__(self, url, id, audio, duration, title, user=None):
        self.urld = url
        self.id = id
        self.audio = audio
        self.user = user # user that requested the song
        self.duration = duration
        self.title = title


def read_token(): 

    # open file
    with open('token.txt') as f:
        # read first line
        token = f.readline()
    
    return token

def fetch_video(videoResult):

    # fetch vid info
    url = videoResult["result"][0]["link"]
    id = videoResult["result"][0]["id"]
    duration = videoResult["result"][0]["duration"]
    title = videoResult["result"][0]["title"]

    # create a new pafy object
    song = pafy.new(id)

    # get audio source
    audio = song.getbestaudio()

    #convert audio source to source that discord can use
    audio = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)

    vid = Video(url, id, audio, duration, title)
    return vid

def is_empty(queue):

    count = 1
    for i in queue:
        count -= 1
        break

    return count


def helper_func():
    playing = False

    return None


# create bot object with prefix !
bot = commands.Bot(command_prefix='!')


# set FFMPEG options
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}


#start playing video immediately (disregard current one)

@bot.event
async def on_ready():

    voiceChannel = None

    while True:
        
        await asyncio.sleep(2)

        if is_empty(videoQueue) == False and (voiceChannel == None or voiceChannel.is_playing() == False):

            try:
                vid = videoQueue.pop()
                vc = vid.user.voice.channel
                voiceChannel = await vc.connect()
                voiceChannel.play(vid.audio, after=helper_func())
            except discord.errors.ClientException: # when bot is already connected
                voiceChannel.play(vid.audio, after=helper_func())

@bot.command()
async def play(ctx, videoName):

    # get vc of msg author
    channel = ctx.author.voice.channel
    vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)

    # fetch video info
    vid = fetch_video(await VideosSearch(videoName, limit = 1).next())
    vid.user = ctx.author
    videoQueue.append(vid)

    #join vc and play audio
    voiceChannel = await vc.connect() 
    voiceChannel.play(vid.audio, after=lambda: print('done'))


# Queue video - Waits for the videos qd before it to finish before playing
@bot.command()
async def queue(ctx, videoName):
    # fetch video info and store in queue
    vid = fetch_video(await VideosSearch(videoName, limit = 1).next())
    vid.user = ctx.author
    vid.ctx = ctx

    if is_empty(videoQueue):
        await ctx.send("Playing video!")
    else:
        await ctx.send("Successfully queued!")

    videoQueue.append(vid)

# Play the next song on the queue
# @bot.command()
# async def play_next(ctx):
#     vid = videoQueue.pop()
#     play_video(vid)


# async def play_video(ctx, vid):
#     print("DEBUG")
#     channel = vid.user.voice.channel
#     vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)
#     voiceChannel = await vc.connect()
#     voiceChannel.play(vid.audio, after=lambda: print('done'))


@bot.command()
async def showQueue(ctx):
    for i, vid in enumerate(videoQueue):
        await ctx.send(str(i) + ": " + vid.title)


# global var - if bot is playing a video
playing = False
# init a queue
videoQueue = deque() # FIFO
# fetch token
token = read_token()
# run bot
bot.run(token)

# TODO commands have a 2nd parameter -> channel in which the bot plays
# TODO only mod+ have access to play command
# TODO embed msges
# TODO progress tracking on showQueue
# TODO skip and pause commands -> only mods+ can skip, pause has a timeout
# TODO current command -> shows info about currently playing video