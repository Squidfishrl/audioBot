# discord modules
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
# yt modules
from youtubesearchpython.__future__ import VideosSearch # async version of the library
import pafy
# other
from collections import deque


class Video:
    def __init__(self, url, id, audio):
        self.urld = url
        self.id = id
        self.audio = audio


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

    # create a new pafy object
    song = pafy.new(id)

    # get audio source
    audio = song.getbestaudio()

    #convert audio source to source that discord can use
    audio = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)

    vid = Video(url, id, audio)
    return vid

# create bot object with prefix !
bot = commands.Bot(command_prefix='!')

# set FFMPEG options
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}


#command definition
@bot.command()
async def play(ctx, videoName):

    # get vc of msg author
    channel = ctx.author.voice.channel
    vc = discord.utils.get(ctx.guild.voice_channels, name=channel.name)

    # fetch video info
    vid = fetch_video(await VideosSearch(videoName, limit = 1).next())

    #join vc and play audio
    voiceChannel = await vc.connect() 
    voiceChannel.play(vid.audio, after=lambda: print('done'))

# fetch token
token = read_token()
# run bot
bot.run(token)