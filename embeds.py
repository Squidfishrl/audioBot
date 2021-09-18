import discord


class Embeds:

    def __init__(self):

        self.basicInfo = None
        self.authorInfo = None
        self.fields = []
        self.embed = None

    def add_main(self, title=None, description=None, titleURL=None, colour=None, footer=None, thumbnailUrl=None):
        self.basicInfo = EmbedMain(title, description, titleURL, colour, footer, thumbnailUrl)

    def add_author(self, name=None, url=None, pfpUrl=None):
        self.authorInfo = EmbedAuthor(name, url, pfpUrl)

    def add_field(self, name=None, value=None, inline=False):

        if len(self.fields) > 10:  # max field amount
            return # TODO raise custom exception
        
        self.fields.append(EmbedField(name, value, inline))

    def create_embed(self):

        if self.basicInfo is not None:

            # add title, title link, description, footer and colour
            if self.basicInfo.colour is not None:
                self.embed = discord.Embed(title=self.basicInfo.title, url=self.basicInfo.titleURL, description=self.basicInfo.description, footer=self.basicInfo.footer, color = self.basicInfo.colour)
            else:
                self.embed = discord.Embed(title=self.basicInfo.title, url=self.basicInfo.titleURL, description=self.basicInfo.description, footer=self.basicInfo.footer)

            if self.basicInfo.footer != None:
                self.embed.set_footer(text=self.basicInfo.footer)

            # add thumbnail
            if self.basicInfo.thumbnailUrl is not None:
                self.embed.set_thumbnail(url=self.basicInfo.thumbnailUrl)


        if self.authorInfo is not None:
            # add author name, nameUrl and pfpUrl
            if self.authorInfo.name is not None:
                if self.authorInfo.url is None and self.authorInfo.pfpUrl is None:
                    self.embed.set_author(name=self.authorInfo.name)
                elif self.authorInfo.url is None:
                    self.embed.set_author(name=self.authorInfo.name, icon_url=self.authorInfo.pfpUrl)
                elif self.authorInfo.pfpUrl is None:
                    self.embed.set_author(name=self.authorInfo.name, url=self.authorInfo.url)
                else:
                    self.embed.set_author(name=self.authorInfo.name, url=self.authorInfo.url, icon_url=self.authorInfo.pfpUrl)

        # add fields
        for field in self.fields:
            self.embed.add_field(name=field.name, value=field.value, inline=field.inline)


class EmbedMain:
    
    def __init__(self, title=None, description=None, titleURL=None, colour=None, footer=None, thumbnailUrl=None):
        self.title = title
        self.description = description
        self.titleURL = titleURL
        self.colour = colour
        self.footer = footer
        self.thumbnailUrl = thumbnailUrl


class EmbedAuthor:

    def __init__(self, name=None, url=None, pfpUrl=None):
        self.name = name
        self.url = url
        self.pfpUrl = pfpUrl


class EmbedField:

    def __init__(self, name="", value="", inline=False):
        self.name=name
        self.value=value
        self.inline=inline


class EmbedColours:

    def __init__(self):
        self.dark_red = 10038562
        self.orange = 16728064
        self.green = 51004