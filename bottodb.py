
import os
import discord
from dotenv import load_dotenv
import random
import mysql.connector
import datetime
import asyncio

#------things to do
#1:there should ba a user table(), watched table, 
# watching table, interested table, and on hold table
#2: lots of exception handling
#3: make the messages into embeds

#---------sql-------
mydb = mysql.connector.connect(
  host="localhost",
  username="root",
  database="anime"
)
cursor= mydb.cursor()

#--------------------------------


#-----------bot stuff------------
load_dotenv()
TOKEN = str(os.getenv("DISCORD_TOKEN"))
guild="bottest"

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True
client = discord.Client(intents=intents)
#confirms that the bot is on
@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == 'bottest':
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

# if user takes too long to respond, operation is cancelled
async def get_user_response(channel):
    def check(m):
        return m.channel == channel and m.author != client.user

    try:
        response = await client.wait_for('message', check=check, timeout=60)  # Wait for 60 seconds for user response
        return response.content
    except asyncio.TimeoutError:
        await channel.send("You took too long to respond. Operation canceled.")
        return None

@client.event
async def on_message(message):
    # program won't act on messages from the bot(client.user)
    if message.author == client.user:
        return
    # checks if meaage starts with !p
    if message.content.startswith("!p"):
        # all bot commands must be 3 parts. otherwise the message won't be acknowledged
        if len(message.content.split(" ")) != 3:
            await message.channel.send("needs to have command and in what table\ne.g:!p insert watched")
            return

        # Split the message into command and table
        msg = message.content.split(" ", 2)
        command = msg[1]
        table = msg[2]
        # Define lists of valid commands and tables
        clist = ["view", "insert", "delete", "edit"]
        tlist = ["watched", "watching", "want_to_watch", "all"]
        # Get the user ID from the message
        user = message.author.id
        # SQL command to insert a new user if not exists
        cmd = """
        INSERT INTO users (username)
        SELECT %s
        WHERE NOT EXISTS (
            SELECT 1 FROM users WHERE username = %s
        )
        """
        cursor.execute(cmd, (user, user))
        
        # Check if the command and table are valid
        if command not in clist and table not in tlist:
            await message.channel.send("invalid command and table name")
            return
        elif command not in clist and table in tlist:
            await message.channel.send("invalid command")
            return
        elif command in clist and table not in tlist:
            await message.channel.send("invalid table name")
            return
        else:
            await message.channel.send("okey")

#----------------------------------insert----------------------------------------------------------
        if command == "insert":
            # SQL insertion commands for the tables
            insertionWatched = f"INSERT INTO watched (name, date_watched, rating, username) VALUES (%s, %s, %s, %s)"
            insertionWatching=f"INSERT INTO watching (name, username, episode) VALUES (%s, %s, %s)"
            insertionWant_to_watch= f"INSERT INTO want_to_watch (name, username) VALUES (%s, %s)"
            # if table is watched user is asked to enter in the name of anime, the day it was watched, and a rating between 0 and 10
            if table=="watched":
                await message.channel.send("enter the name of the anime")
                anime_name = await get_user_response(message.channel)
                if not anime_name:
                    return  # Operation canceled due to timeout
               # checks if date given is in the correct format
                await message.channel.send("enter the time when u finished it(format: YYYY-MM-DD)")
                date = await get_user_response(message.channel)
                if not date:
                    return  # Operation canceled due to timeout

                valid = False
                while not valid:
                    try:
                        datetime.date.fromisoformat(date)
                    except ValueError:
                        await message.channel.send("invalid. enter the date u finished the anime(format: YYYY-MM-DD)")
                        date = await get_user_response(message.channel)
                        if not date:
                            return  # Operation canceled due to timeout
                    else:
                        valid = True
                # ratings are rounded to 1 deciman place 
                await message.channel.send("enter a rating out of 10(numbers will be rounded to 1 decimal place)")
                rating_response = await get_user_response(message.channel)
                if not rating_response:
                    return  # Operation canceled due to timeout

                rating = float(rating_response)
                rating = round(rating, 1)
                #if lower than 0 or higher than 10 it'll be changed to 0 or 10 respectively
                if rating < 0:
                    print("o3o...i'll change it to 0 ")
                    rating = 0
                elif rating > 10:
                    print("owo...i'll change it to 10 ")
                    rating = 10
                # the inputted values are added to the watched table in the database
                val = (anime_name, date, rating, user)
                cursor.execute(insertionWatched, val)
                mydb.commit()
                await message.channel.send("done")
#-----------------------------------------
            elif table == "watching":
                # the name and current episode are requested from the user
                await message.channel.send("enter the name of the anime")
                anime_name = await get_user_response(message.channel)
                if not anime_name:
                    return  # Operation canceled due to timeout

                await message.channel.send("enter current episode")
                episode=await get_user_response(message.channel)
                if not episode:
                    return  # Operation canceled due to timeout
                # the inputted values are added to the watching table in the database
                val=(anime_name, user, episode)
                cursor.execute(insertionWatching, val)
                mydb.commit()
                await message.channel.send("done")
#-----------------------------------------
            elif table == "want_to_watch":
                await message.channel.send("enter the name of the anime")
                anime_name = await get_user_response(message.channel)
                if not anime_name:
                    return  # Operation canceled due to timeout

                val=(anime_name, user)
                cursor.execute(insertionWant_to_watch, val)
                mydb.commit()
                await message.channel.send("done")
            else:
                await message.channel.send("Invalid")
                return


            
#--------------------------------------------------------------------------------------------
        #outputs all the results in a specific table on discord
        elif command == "view":
            viewWatched = "SELECT name, date_watched, rating FROM watched WHERE username = %s"
            viewWatching="SELECT name, episode FROM watching WHERE username = %s"
            viewWant_to_watch="SELECT name FROM want_to_watch WHERE username = %s"
            
            if table=="watching":
                cursor.execute(viewWatching,[user])
                for x in cursor:
                    await message.channel.send(x)
            elif table == "watched":
                cursor.execute(viewWatched,[user])
                for x in cursor:
                    await message.channel.send(x)
            elif table =="want_to_watch":
                cursor.execute(viewWant_to_watch,[user])
                for x in cursor:
                    await message.channel.send(x)
            else:
                await message.channel.send("invalid command")


                
#--------------------------------------------------------------------------------------------
        elif command == "delete":
            # delete user from database completely
            # delete rows from a table
            if table== "all":
                await message.channel.send("are you sure?(y)")
                opt = await get_user_response(message.channel)
                # deletes all values from all tables for the current user
                if opt=="y":
                    val=[user]
                    cursor.execute("DELETE FROM watching WHERE username= %s", val)
                    cursor.execute("DELETE FROM watched WHERE username= %s", val)
                    cursor.execute("DELETE FROM want_to_watch WHERE username= %s", val)
                    cursor.execute("DELETE FROM users WHERE username= %s", val)
                    mydb.commit()
                    await message.channel.send("done")
                else:
                    await message.channel.send("Operation cancelled")
                    return
            elif table=="watching":
                # asks user if they want to delete the whole table or one entry for watching
                await message.channel.send("everything(all) or one entry(one)")
                opt=await get_user_response(message.channel)
                if opt=="all":
                    cursor.execute("DELETE FROM watching WHERE username= %s",(user))
                elif entry=="one":
                    await message.channel.send("everything(all) or one entry(one)")
                    aniDelName=await get_user_response(message.channel)
                    cursor.execute("DELETE FROM watching WHERE username= %s AND name=%s",(user,aniDelName))
                else:
                    await message.channel.send("Operation cancelled")
                    return
               
            elif table =="watched":
                # asks user if they want to delete the whole table or one entry for watched
                await message.channel.send("everything(all) or one entry(one)")
                opt=await get_user_response(message.channel)
                if opt=="all":
                    cursor.execute("DELETE FROM watched WHERE username= %s",(user))
                elif entry=="one":
                    await message.channel.send("everything(all) or one entry(one)")
                    aniDelName=await get_user_response(message.channel)
                    cursor.execute("DELETE FROM watched WHERE username= %s AND name=%s",(user,aniDelName))
                else:
                    await message.channel.send("Operation cancelled")
                    return
            else:
                # asks user if they want to delete the whole table or one entry for want to watch
                await message.channel.send("everything(all) or one entry(one)")
                opt=await get_user_response(message.channel)
                if opt=="all":
                    cursor.execute("DELETE FROM want_to_watch WHERE username= %s",(user))
                elif entry=="one":
                    await message.channel.send("everything(all) or one entry(one)")
                    aniDelName=await get_user_response(message.channel)
                    cursor.execute("DELETE FROM want_to_watch WHERE username= %s AND name=%s",(user,aniDelName))
                else:
                    await message.channel.send("Operation cancelled")
                    return
            
#--------------------------------------------------------------------------------------------

        
    if message.content == "!help":
        #prints a message that like has all the commands and table names
        await message.channel.send("!p\n**commands**\nview, delete, insert\n**tables**\nwatched, watching, want_to_watch")
        return

# runs the bot
client.run(TOKEN)


    