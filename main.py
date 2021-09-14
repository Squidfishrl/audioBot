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
        self.url = url
        self.id = id
        self.audio = audio
        self.user = user # user that requested the song
        self.duration = duration
        self.title = title
        self.voiceChannel = None # vc that the bot is connected to


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


# constantly try to loop vids if there r any
@bot.event
async def on_ready():

    voiceChannel = None

    while True:
        
        await asyncio.sleep(1)

        if voiceChannel is not None and voiceChannel.is_playing() == False:
            bot.currentPlaying = None

        if is_empty(bot.videoQueue) == False and (voiceChannel == None or voiceChannel.is_playing() == False):

            # remove vid from queue
            vid = bot.videoQueue.pop()

            try:
                
                vc = vid.user.voice.channel
                voiceChannel = await vc.connect()

                bot.currentPlaying = vid
                bot.currentPlaying.voiceChannel = voiceChannel

                voiceChannel.play(vid.audio, after=lambda x: False) # TODO change to send a msg that its playing smth
            except discord.errors.ClientException: # when bot is already connected
                bot.currentPlaying = vid
                bot.currentPlaying.voiceChannel = voiceChannel
                voiceChannel.play(vid.audio, after=lambda x: False)

            
                    
#start playing video immediately (disregard current one)
@bot.command()
async def play(ctx, videoName):

    # get vc of msg author
    channel = ctx.author.voice.channel
    vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)

    # fetch video info
    vid = fetch_video(await VideosSearch(videoName, limit = 1).next())
    vid.user = ctx.author
    bot.videoQueue.append(vid)

    #join vc and play audio
    voiceChannel = await vc.connect() 
    voiceChannel.play(vid.audio, after=lambda: print('done'))


# Queue video - Waits for the videos qd before it to finish before playing
@bot.command()
async def queue(ctx, videoName):
    # fetch video info and store in queue
    vid = fetch_video(await VideosSearch(videoName, limit = 1).next())
    vid.user = ctx.author

    await ctx.send("Successfully queued!")

    bot.videoQueue.append(vid)


# Stops playing the current vid
@bot.command()
async def skip(ctx):
    if is_empty(bot.videoQueue):
        await ctx.send("Video queue is already empty!")
    else:
        if bot.currentPlaying is None:
            await ctx.send("Next vid hasnt started yet!")
            return

        bot.currentPlaying.voiceChannel.stop() # stop playing audio
        await ctx.send("Skipped video!")
            
# Play the next song on the queue
# @bot.command()
# async def play_next(ctx):
#     vid = bot.videoQueue.pop()
#     play_video(vid)


# async def play_video(ctx, vid):
#     print("DEBUG")
#     channel = vid.user.voice.channel
#     vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)
#     voiceChannel = await vc.connect()
#     voiceChannel.play(vid.audio, after=lambda: print('done'))


@bot.command()
async def showQueue(ctx):
    await ctx.send("Video Queue: \n")
    if bot.currentPlaying is not None:
        await ctx.send("CURRENT: " + bot.currentPlaying.title + " " + bot.currentPlaying.duration)
    for i, vid in enumerate(bot.videoQueue):
        await ctx.send(str(i+1) + ": " + vid.title + " " + vid.duration)




bot.currentPlaying = None
# init a queue
bot.videoQueue = deque() # FIFO
# fetch token
token = read_token()
# run bot
bot.run(token)

# 14.09
# DONE global var that contains info on the current playing video or is None if video isnt playing
# TODO commands have a 2nd parameter -> channel in which the bot plays
# TODO only mod+ have access to play command
# TODO embed msges
# TODO progress tracking on showQueue
# TODO skip and pause commands -> only mods+ can skip, pause has a timeout
# TODO current command -> shows info about currently playing video
# TODO have a setting which saves the queue in a file and reads from there if the queue is empty, and u can create a playlist