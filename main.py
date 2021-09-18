# discord modules
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
# yt modules
from youtubesearchpython.__future__ import CustomSearch, VideoSortOrder # async version of the library
import pafy
# other
from embeds import *
from collections import deque
import asyncio
import datetime

class Video:
    def __init__(self, url, id, audio, duration, title, views, publishTime, thumbnail, channelName, channelLink, channelPfp, description=None, user=None):
        self.url = url
        self.id = id
        self.audio = audio
        self.user = user # user that requested the song
        self.duration = duration
        self.title = title
        self.views = views
        self.voiceChannel = None # vc that the bot is connected to
        self.description = description
        self.publishTime = publishTime
        self.thumbnail = thumbnail
        self.startPlayTime = None # time of when song started playing
        self.channel = None # channel from which user queued the video
        # channel related:
        self.channelName = channelName
        self.channelLink = channelLink
        self.channelPfp = channelPfp


def read_token(): 

    # open file
    with open('token.txt') as f:
        # read first line
        token = f.readline()
    
    return token

def fetch_video(videoResult):

    # fetch vid info
    videoResult = videoResult["result"][0]
    url = videoResult["link"]
    id = videoResult["id"]
    duration = videoResult["duration"]
    title = videoResult["title"]
    views = videoResult["viewCount"]["text"]
    views = views.split(' ')[0]
    publishTime = videoResult["publishedTime"]
    description = videoResult["descriptionSnippet"][0]["text"]
    thumbnail = videoResult["thumbnails"][0]["url"]
    # fetch vid creator info
    creator = videoResult["channel"]["name"]
    creatorLink = videoResult["channel"]["link"]
    creatorPfp = videoResult["channel"]["thumbnails"][0]["url"]

    if duration == None:
        return None

    duration = datetime.datetime.strptime(duration, "%M:%S")
    duration = duration - datetime.datetime.strptime("00:00", "%M:%S")

    # create a new pafy object
    song = pafy.new(id)
    # get audio source
    audio = song.getbestaudio()

    #convert audio source to source that discord can use
    audio = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)

    vid = Video(
        url=url, 
        id=id,
        audio=audio,
        duration=duration,
        title=title,
        views=views,
        publishTime=publishTime,
        thumbnail=thumbnail,
        channelName=creator,
        channelLink=creatorLink,
        channelPfp=creatorPfp,
        description=description)

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
            print("Playing rn")
            try:
                
                vc = vid.user.voice.channel
                voiceChannel = await vc.connect()

                bot.currentPlaying = vid
                bot.currentPlaying.voiceChannel = voiceChannel

                voiceChannel.play(vid.audio, after=lambda x: False) # TODO Try to play again immediately after 
            except discord.errors.ClientException: # when bot is already connected
                bot.currentPlaying = vid
                bot.currentPlaying.voiceChannel = voiceChannel
                voiceChannel.play(vid.audio, after=lambda x: False)

            bot.currentPlaying.startPlayTime = datetime.datetime.now()

                    
#start playing video immediately (disregard current one)
@bot.command()
@commands.has_guild_permissions(mute_members=True)
async def force(ctx, *, arg):

    if bot.unlimitedParameters == False:
        videoNames = []
        videoNames.append(str(arg))
    else:
        videoNames = arg.split(bot.paramSeparator)

    for b, videoName in enumerate(videoNames):
        b += 1
        print(b)
    # get vid

        try:
            vid = fetch_video(await CustomSearch(videoNames[-b], VideoSortOrder.viewCount, limit = 1).next())
        except IndexError:

            # error message
            embed = Embeds()
            embed.add_main(
                title="No results found",
                description="Note: Only videos on youtube can be played",
                colour=EmbedColours().orange
            )
            embed.add_author(
                name="Error"
            )
            embed.create_embed()

            await ctx.send(embed=embed.embed)
            return

        vid.user = ctx.author
        vid.channel = ctx.channel

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
        try:
            vid = fetch_video(await CustomSearch(videoName, VideoSortOrder.viewCount, limit = 1).next())
        except IndexError:
            # error message
            embed = Embeds()
            embed.add_main(
                title="No results found",
                description="Note: Only videos on youtube can be played",
                colour=EmbedColours().orange
            )
            embed.add_author(
                name="Error"
            )
            embed.create_embed()

            await ctx.send(embed=embed.embed)
            return

        vid.user = ctx.author
        vid.channel = ctx.channel

        bot.videoQueue.append(vid)

    # success message
    embed = Embeds()

    embed.add_main(
        title="**Success!**",
        colour=EmbedColours().green,
    )
    embed.create_embed()
    await ctx.send(embed=embed.embed)  


# Stops playing the current vid
@bot.command()
async def skip(ctx):

    if bot.currentPlaying is None:
        # error message
        embed = Embeds()
        embed.add_main(
            title="!skip has no effect when no video is played.",
            description="Note: It may take up to 1 second for the next queued video to play",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return

    bot.currentPlaying.voiceChannel.stop() # stop playing audio
    
    # success message
    embed = Embeds()

    embed.add_main(
        title="**Success!**",
        colour=EmbedColours().green,
    )
    embed.create_embed()
    await ctx.send(embed=embed.embed)         


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

    if bot.currentPlaying is None:
        # error message
        embed = Embeds()
        embed.add_main(
            title="!current has no effect when no video is played.",
            description="Note: It may take up to 1 second for the next queued video to play",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return
    
    # calculate elapsed time
    timePassed = datetime.datetime.now() - bot.currentPlaying.startPlayTime

    # calculate percent elapsedTime/vidDuration
    secondsPassed = int(timePassed.total_seconds())
    vidDurationSec = int(bot.currentPlaying.duration.total_seconds())
    timeElapsedPercent = (secondsPassed / vidDurationSec) * 100
    timeElapsedPercent = round(timeElapsedPercent, 2)

    # convert to str and format to look better
    vidDuration = str(bot.currentPlaying.duration)
    while(vidDuration[0] == '0' or vidDuration[0] == ':'):
        vidDuration = vidDuration[1:]

    timePassed = timePassed - datetime.timedelta(microseconds=timePassed.microseconds)
    timePassed = str(timePassed)
    while(len(timePassed) > len(vidDuration)):
        timePassed = timePassed[1:]

    # create embed and send
    embed = Embeds()
    embed.add_main(
        title=bot.currentPlaying.title,
        description=bot.currentPlaying.description,
        titleURL=bot.currentPlaying.url,
        colour=EmbedColours().dark_red,
        thumbnailUrl=bot.currentPlaying.thumbnail
    )
    embed.add_author(
        name=bot.currentPlaying.channelName,
        url=bot.currentPlaying.channelLink,
        pfpUrl=bot.currentPlaying.channelPfp
    )

    embed.add_field(
        name='\u200b',
        value="**Time Elapsed:  **" + timePassed + "/" + vidDuration + "  (" + str(timeElapsedPercent) + "%)"
    )

    embed.add_field(
        name='\u200b',
        value="**Views: **" + bot.currentPlaying.views
    )

    embed.add_field(
        name='\u200b',
        value= "**Release date:  **" + bot.currentPlaying.publishTime
    )

    embed.create_embed()
    await ctx.send(embed=embed.embed)

# pause audio if one is playing
@bot.command()
async def pause(ctx):

    if bot.currentPlaying is None:
        # error message
        embed = Embeds()
        embed.add_main(
            title="!pause has no effect when no video is played.",
            description="Note: It may take up to 1 second for the next queued video to play",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return

    if bot.currentPlaying.voiceChannel.is_paused():
        # error message
        embed = Embeds()
        embed.add_main(
            title="!pause has no effect when video is already paused.",
            description="Note: use !resume to resume the video",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return

    bot.currentPlaying.voiceChannel.pause()

    # success message
    embed = Embeds()

    embed.add_main(
        title="**Success!**",
        colour=EmbedColours().green,
    )
    embed.create_embed()
    await ctx.send(embed=embed.embed)



# resume audio if paused
@bot.command()
async def resume(ctx):

    if bot.currentPlaying is None:

        # error message
        embed = Embeds()

        embed.add_main(
            title="!resume has no effect when no video is played.",
            description="Note: It may take up to 1 second for the next queued video to play",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return

    if bot.currentPlaying.voiceChannel.is_paused() == False:

        # error message
        embed = Embeds()

        embed.add_main(
            title="!resume has no effect when video isn't paused.",
            description="Note: use !pause to pause the video",
            colour=EmbedColours().orange
        )
        embed.add_author(
            name="Invalid usage"
        )
        embed.create_embed()

        await ctx.send(embed=embed.embed)
        return


    bot.currentPlaying.voiceChannel.resume()

    # success message
    embed = Embeds()

    embed.add_main(
        title="**Success!**",
        colour=EmbedColours().green,
    )
    embed.create_embed()
    await ctx.send(embed=embed.embed)  


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
# 16.09
# DONE create Embed class for easier embed creation
# 18.09
# DONE add embedMsges to !current, !pause, !resume, !skip, !queue
# TODO embed msges and more error msges
# TODO progress tracking on showQueue and improved !currend (with %)
# TODO add error msg for !force if no perms
# TODO if nothing is playing and !skip is used, try to remove first vid on queue if possible
# TODO add another parameter to !skip, allowing u to skip multiple vids at once
# TODO skip and pause commands perms -> only mods+/authors can skip, pause has a timeout
# TODO OPT add custom exceptions which create embed msges automatically and send (or functions instead of exceptions)
# TODO !help -> explaining all commands in detail
# TODO save and load settings
# TODO have a setting which saves the queue in a file and reads from there if the queue is empty, and u can create a playlist
# TODO idk if its possible but try to handle https request errors or atleast say a msg that one occured