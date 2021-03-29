# VolumioRPC

VolumioRPC is a quick script that I wrote for setting your Discord "Now playing"-status to what is playing on any device running [Volumio](https://volumio.org) on your network.

I wrote the script for my needs, which was showing what is playing (or not playing) on the connected Volumio devices. Therefore, these are the available states (currently):
* Playing back
* Paused/Stopped
* Idle 
* Other state (not parsed)

### Prerequisites
* A [Discord application](https://developer.discord.com/). Copy the client ID.

### Setup

It is very simple to get started! Just download clone the repository to your local machine and then follow these steps:

#### Install dependencies

Install `requests` and `pypresence` with `pip`.

#### Edit the configuration file.

The script loads a configuration file called `config.json`.
There should only be two things that you have to edit:
* `discord/client_id`: The Client ID of the Discord application that you created earlier. 
  > ⚠ **Note:** Put the client ID in as a string!
* `volumio/base_url`: The base URL for your Volumio instance. Change this if it is anything else than the default `volumio.local`.
    > ⚠ **Note:** Be sure to include a protocol (`http://` or `https://`), otherwise, any requests to Volumio will fail and the script now work.

#### Images

You probably would like to have images in your presence.
You can use the ones provided in the "images" folder in this project.
The images has to be uploaded to the same [Discord application](https://developer.discord.com/) as the one you are using the client ID for.

The default images are from [MaterialDesignIcons](https://materialdesignicons.com), upscaled via [BigJPG](bigjpg.com).
> ℹ You can upload images under "Rich presence > Rich presence assets" in the Discord Developer Console.

The files provided have their default names that the RPC uses, but if you want to change these names, you can do so under `discord/image_names` in the configuration file.

> 💡 **Pro tip:** You can use `null` to hide images if you don't want to display them in a certain state.

#### Changing the update interval

The default update interval for the script is 15 seconds, meaning generally one request to the Volumio device and Discord's RPC
every 15 seconds + one additional request when the script starts. 
> ℹ **Note:** It is possible that each update requires more than just one request, especially if the hostname fails to resolve. However, the script has not implemented specific code for retrying any requests to the Volumio interface, that would if so be done by the `requests` library.

If you want to change this value, you can change the `update_interval`-parameter in the configuration file.

> ℹ **Note:** The `update_interval` parameter should be in seconds.
