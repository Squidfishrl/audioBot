# discord modules
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
# yt modules
from youtubesearchpython.__future__ import CustomSearch, VideoSortOrder # async version of the library
import pafy
# other
from collections import deque
import asyncio
from datetime import datetime
class Video:
    def __init__(self, url, id, audio, duration, title, user=None):
        self.url = url
        self.id = id
        self.audio = audio
        self.user = user # user that requested the song
        self.duration = duration
        self.title = title
        self.voiceChannel = None # vc that the bot is connected to
        self.startPlayTime = None # time of when song started playing


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

    if duration == None:
        return None

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

        if voiceChannel is not None and voiceChannel.is_playing() == False and voiceChannel.is_paused() == False:
            bot.currentPlaying = None

        if is_empty(bot.videoQueue) == False and (voiceChannel == None or (voiceChannel.is_playing() == False and voiceChannel.is_paused() == False)):

            # remove vid from queue
            vid = bot.videoQueue.popleft() # q head is always left

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

            bot.currentPlaying.startPlayTime = datetime.now()

            
                    
#start playing video immediately (disregard current one)
@bot.command()
@commands.has_guild_permissions(mute_members=True)
async def force(ctx, *, arg):

    if bot.unlimitedParameters == False:
        videoNames = []
        videoNames.append(str(arg))
    else:
        videoNames = arg.split(bot.paramSeparator)
        print(type(videoNames))

    for b, videoName in enumerate(videoNames):
        b += 1
        print(b)
    # get vid

        vid = fetch_video(await CustomSearch(videoNames[-b], VideoSortOrder.viewCount, limit = 1).next())

        vid.user = ctx.author

        # add to queue on the left
        bot.videoQueue.appendleft(vid)

    # skip current
    if bot.currentPlaying is not None:
        bot.currentPlaying.voiceChannel.stop()

    await ctx.send("Successfully forced!")


# Queue video - Waits for the videos qd before it to finish before playing
@bot.command()
async def queue(ctx, *, arg):

    if bot.unlimitedParameters == False:
        videoNames = []
        print(arg)
        videoNames.append(str(arg))
    else:
        videoNames = arg.split(bot.paramSeparator)
    

    for videoName in videoNames:

        # fetch video info and store in queue
        vid = fetch_video(await CustomSearch(videoName, VideoSortOrder.viewCount, limit = 1).next())

        vid.user = ctx.author

        bot.videoQueue.append(vid)
    
    await ctx.send("Successfully queued!")


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


# Prints all Queued songs along current one
@bot.command()
async def showQueue(ctx):

    msg = ""

    msg = ("Video Queue: \n")
    if bot.currentPlaying is not None:
        msg += "CURRENT: " + bot.currentPlaying.title + " " + bot.currentPlaying.duration
    for i, vid in enumerate(bot.videoQueue):
        msg += "\n" + str(i+1) + ": " + vid.title + " " + vid.duration


    if msg == "":
        msg = "Video Queue is empty"
    await ctx.send(msg)


@bot.command()
async def unlParams(ctx):
    # allows you to pass multiple songs to queue in the same command
    # example !queue "Song 1" "Song 2" "Song 3" #ChannelA
    # if its off you can mostly do !queue "Song 1" #ChannelA
    bot.unlimitedParameters = False if bot.unlimitedParameters else True
    await ctx.send("Unlimited parameters is now set to " + str(bot.unlimitedParameters))


# show extra info on current playing song
@bot.command()
async def current(ctx):

    if current is None:
        await ctx.send("no video is playing atm (if there is a song queued it can take up to a second for it to start playing)")
        return
    
    msg = ""
    msg += bot.currentPlaying.url + "\n"
    timePassed = str(datetime.now() - bot.currentPlaying.startPlayTime).split('.')[0]
    msg += timePassed + "/" + bot.currentPlaying.duration

    await ctx.send(msg)


# pause audio if one is playing
@bot.command()
async def pause(ctx):

    if bot.currentPlaying is None:
        await ctx.send("No video playing atm")
        return

    if bot.currentPlaying.voiceChannel.is_paused():
        await ctx.send("video already paused")
        return

    bot.currentPlaying.voiceChannel.pause()
    await ctx.send("video paused!")    


# resume audio if paused
@bot.command()
async def resume(ctx):
    if bot.currentPlaying is None:
        await ctx.send("No video playing atm")
        return

    if bot.currentPlaying.voiceChannel.is_paused() == False:
        await ctx.send("video isnt paused")
        return

    bot.currentPlaying.voiceChannel.resume()
    await ctx.send("video resumed!")    


# init a queue
bot.videoQueue = deque() # FIFO
bot.currentPlaying = None # video info thats being played now

# init global settings
bot.unlimitedParameters = False
bot.paramSeparator = ','

# fetch token
token = read_token()
# run bot
bot.run(token)

# 14.09
# DONE global var that contains info on the current playing video or is None if video isnt playing
# DONE add skip command
# DONE make play command overwrite current audio and rename to force 
# 15.09
# DONE option to turn on unl parameters to then queue/force.
# DONE current command which shows extra info on current song
# DONE pause/resume command
# DONE req mute permissions to use !force command
# TODO embed msges and more error msges
# TODO progress tracking on showQueue and improved !currend (with %)
# TODO idk if its possible but try to handle https request errors or atleast say a msg that one occured
# TODO skip and pause commands perms -> only mods+/authors can skip, pause has a timeout
# TODO save and load settings
# TODO have a setting which saves the queue in a file and reads from there if the queue is empty, and u can create a playlist