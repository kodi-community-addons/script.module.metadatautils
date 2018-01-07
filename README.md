## plugin.audio.roon - Kodi add-on for Roon

Unofficial Kodi addon for Roon (roonlabs.com) with basic browsing and playback control.


## Installation

For now, the python code of this add-on is not directly talking to the Roon api as there is not yet a python SDK/API released by Roon itself, or proper documentation about the websockets API.
So for the time being a intermediate webservice is used which talks to the nodeJS api making it available as restfull services for the python code.
It's my plan to replace this by direct api calls once I get some more info about the websockets api that Roon provides.


1. Download and install the webproxy
    Download and install the api proxy nodeJS module from https://github.com/marcelveldt/roon-extension-api-proxy
    Make sure it's up and running (by default on port 3006) before you continue !


2. Download/install my repository

   * Download my respository setup file as zip: 

   https://github.com/marcelveldt/repository.marcelveldt/raw/master/repository.marcelveldt/repository.marcelveldt-1.0.1.zip

   * Install the repository add-on in Kodi with the "install from ZIP" method.

   * My repository with addons I develop should now be available in Kodi.


3. Install the Roon add-on in Kodi

   * Once you have my repository set-up in Kodi, you can simply navigate the repo in the add-on browser and install the Roon add-on from there.

   * Because you install from the repo, it will be auto updated when there are changes.


4. Configure the add-on

    * At first launch you need to provide the hostname and port to the special proxy application you installed at step 1.
    * You can enter these details at first launch of the addon or later if you open the addon settings.


5. Done !

    You can now browse your Roon library from within Kodi and start playback on a selected zone.
    For basic playback control, I've also included a fullscreen OSD.


## What is supported ?

* All basic player commands are supported, like controlling the volume, play/pause, next etc.
* You can select which zone to control from within the mainmenu and the contextmenu.
* Only basic info is provided by the Roon api, so no genre, ratings etc.
* There is no playback support, you simply control existing Roon zones.
* There is playlist management, as it is not provided by the api.
* There is no way to see the queue, as it is not provided by the api.


## Feedback and TODO

This is considered to be a work in progress. I'm sure there will be some bugs in the code somewhere.
Let's test it, fix it and when stable enough submit it to Kodi for inclusion in the official repo (with Roon's approval offcourse).

Please use the Roon forum to discuss the progress:

https://community.roonlabs.com/t/kodi-addon-for-roon


TO-DO:

* Connect to Roon websockets api directly instead of using the nodeJS proxy.
* Some more styling to the fullscreen OSD
* Find a way to get more metadata
* cleanup code / pep8 compliance






