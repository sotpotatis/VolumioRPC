'''
VolumioRPC
Super-simple (but working) Discord Rich Presence for displaying what is currently playing on a local or remote device running Volumio.
For requirements, see requirements.txt.
Made by sotpotatis with <3
'''

#Imports
from pypresence import Presence
import logging, requests, time, os, json
'''VolumioRPC uses a configurable configuration file in order to work.
The file format is in JSON and the file should be located in the same directory as the script.
If you get any errors such as JSONDecodeError, it is most likely due to the fact that your JSON file is malformatted.'''

logging.getLogger().setLevel(logging.DEBUG) #Set the log level

#Load parameters related to the configuration file
SCRIPT_DIRECTORY = os.path.dirname(__file__) #Get the parent directory of where the script is running
logging.debug(f"Script parent directory: {SCRIPT_DIRECTORY}")
CONFIGURATION_FILEPATH = os.path.join(SCRIPT_DIRECTORY, "config.json") #The configuration file path
logging.debug(f"Script configuration filepath: {CONFIGURATION_FILEPATH}")
logging.info("Loading configuration file...")
CONFIGURATION = json.loads(open(CONFIGURATION_FILEPATH, "r").read()) #Load the configuration file
logging.info("Configuration file loaded.")

#Load configuration parameters'
'''Configuration for Discord is under the "discord" key in the JSON.
Configuration for Volumio is under the "volumio" key in the JSON.
General configuration is not in any subarray.'''
DISCORD_CONFIGURATION = CONFIGURATION["discord"]
VOLUMIO_CONFIGURATION = CONFIGURATION["volumio"]

CLIENT_ID = DISCORD_CONFIGURATION["client_id"]
#Load image names from the configuration file
DISCORD_IMAGE_NAMES = DISCORD_CONFIGURATION["image_names"]
LARGE_IMAGE_NAME = DISCORD_IMAGE_NAMES["large_image"]
PLAYING_IMAGE_NAME = DISCORD_IMAGE_NAMES["playing"]
PAUSED_IMAGE_NAME = DISCORD_IMAGE_NAMES["paused"]
IDLE_IMAGE_NAME = DISCORD_IMAGE_NAMES["idle"]
OTHER_IMAGE_NAME = DISCORD_IMAGE_NAMES["other"]
VOLUMIO_URL = VOLUMIO_CONFIGURATION["base_url"]
UPDATE_INTERVAL = CONFIGURATION["update_interval"] #In seconds

logging.info("Configuration parameters loaded.")

#Initialize a presence and connect to Discord
p = None #Global Prensence object
def connect_to_discord():
    '''Connection code for Discord.
    Also clears the current presence in case the app is restarted and Discord
    still assumes the old state.'''
    global p #Use the global presence variable
    p = Presence(client_id=CLIENT_ID)
    logging.info("Connecting to Discord...")
    p.connect()
    logging.info("Connected.")
    logging.debug("Clearing presence...")
    p.clear() #Clear the presence
    logging.debug("Presence cleared.")

logging.info("Initializing Discord connection...")
connect_to_discord() #Connect to Discord
#Generate URLs
NOW_PLAYING_URL = f"{VOLUMIO_URL}/api/v1/getState"
SYSTEM_URL = f"{VOLUMIO_URL}/api/v1/getSystemVersion"

logging.info("Sending request to Volumio for system status...")
try:
    system_status = requests.get(SYSTEM_URL).json()
    system_version = system_status["systemversion"]
    system_variant = system_status["variant"]
    system_hardware = system_status["hardware"]
    logging.info("Volumio state retrieved.")
    #Generate a system version info string
    LARGE_TEXT = f"{system_variant.capitalize()} v{system_version} on hardware \"{system_hardware.capitalize()}\""
except Exception as e: #System status was not available on my older Volumio version, so we can skip it actually for those.
    logging.warning("System status not available! (are you running an old Volumio versioner)?", exc_info=True)
    LARGE_TEXT = "Volumio - The Audiophile Music Player"

logging.info("Starting main loop!")

prev_state = None #Save the previous state
while True: #Run forever until the script is stopped
    logging.info("Retrieving playing status from Volumio...")
    playing_status = requests.get(NOW_PLAYING_URL).json() #Send a request to Volumio's Now Playing URL
    logging.debug(f"Volumio response: {playing_status}.")
    logging.info("Playing status retrieved.")

    #Check the status
    playback_status = playing_status["status"]
    if prev_state != playback_status:
        logging.info("New status found!")
        starting_time = time.time() #Change the start time (since we started a new activity)

    if playback_status == "play": #If the music player is playing
        #NOTE: Ironically, this state can also be that the player is idle, but the script is able to detect an idling interface at a later stage.
        logging.info("Parsed state: Playing back.")
        state = "Playing back"
        small_image_name = PLAYING_IMAGE_NAME

    elif playback_status == "stop": #If the music player is currently stopped.
        logging.info("Parsed state: Paused/stopped.")
        state = "Paused"
        small_image_name = PAUSED_IMAGE_NAME

    else: #If we get to a state that is not known by the script.
        logging.warning(f"Status {playing_status} classified as \"other\". (not included in parsing)")
        state = playing_status.capitatlize() #Set the user's state to the raw status as returned by Volumio, but capitalized
        small_image_name = OTHER_IMAGE_NAME #Use the other small image
    logging.debug(f"Parsed state text: {state}.")

    '''Now, generate a string for now playing details.
    The string will try to include as much information as possible.
    If no title or artist is currently playing, the status for the user will be classified
    as "idling".
    '''
    now_playing_str = "" #Start with an empty string

    #Retrieve track details
    title = playing_status["title"]
    artist = playing_status["artist"]
    album = playing_status["album"] #NOTE: This is currently unused

    #Try to add detail to the now playing string
    #(Volumio returns empty strings and not null (None) when now playing information is not available.
    if len(title) > 0: now_playing_str += title #If a title is available
    if len(artist) > 0: now_playing_str += f" - {artist}" #If an artist is available

    #Generate the details text in the presence
    if len(now_playing_str) > 0: #If details were able to be retrieved
        logging.info(f"Now playing found! Generated string: {now_playing_str}.")
        details = now_playing_str
    else: #If no current playing metadata is available
        logging.info("No playing metadata found.")
        #Even if the state might be playing, but no media can be found, we can assume the media player is idling
        logging.info("Assuming idling state!")
        state = "Idling"
        small_image_name = IDLE_IMAGE_NAME
        details = None

    #Update presence data
    logging.info(f"Updating presence with state {state} and details {details}.")
    error = False
    try:
        p.update(
        state=state,
        details=details,
        large_image=LARGE_IMAGE_NAME,
        large_text=LARGE_TEXT,
        small_image=small_image_name,
        small_text=state, #Use the state text, eg. "Playing back" as the text for the small text
        start=starting_time
        )
        logging.info("Status successfully updated.")
    except Exception as e:
        error = True
        '''Sounds fair to catch Discord-related errors but not Volumio-related errors,
        since Volumio-related errors will make this script not be able to meet its purpose...'''
        logging.critical(f"Failed to send a presence update to Discord! Error: {e}", exc_info=True)
        logging.info("TIP: Make sure that your Discord presence is running and that your firewall is not blocking the connection.")
        logging.info("The script will automatically try to update again in the set update interval.")
    logging.info("Waiting until next update...")
    logging.debug(f"Waiting {UPDATE_INTERVAL} seconds.")
    time.sleep(UPDATE_INTERVAL)
    #If an error occurred, attempt a reconnect
    if error:
        logging.info("Attempting a reconnetion to Discord...")
        try:
            connect_to_discord()
        except Exception as e:
            logging.critical(f"Error: Reconnection to Discord failed with exception: {e}", exc_info=True)
