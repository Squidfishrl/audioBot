# discord modules
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
# yt modules
from youtubesearchpython.__future__ import VideosSearch # async version of the library
import pafy


def read_token(): 

    # open file
    with open('token.txt') as f:
        # read first line
        token = f.readline()
    
    return token


# create bot object with prefix !
bot = commands.Bot(command_prefix='!')

# set FFMPEG options
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}


#command definition
@bot.command()
async def play(ctx, videoName):
    
    # resend videoName parameter (msg user sends after !play)
    await ctx.channel.send(videoName)
    
    # fetch first video that matches videoName
    videoResult = await VideosSearch(videoName, limit = 1).next()
    url = videoResult["result"][0]["link"]
    id = videoResult["result"][0]["id"]
    await ctx.channel.send(url)

    # get vc of msg author
    channel = ctx.author.voice.channel
    vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)


    # create a new pafy object
    song = pafy.new(id)

    # get audio source
    audio = song.getbestaudio()
    print(audio.url)

    #convert audio source to source that discord can use
    audio = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)

    #join vc and play audio
    voiceChannel = await vc.connect() 
    voiceChannel.play(audio)

# fetch token
token = read_token()
# run bot
bot.run(token)