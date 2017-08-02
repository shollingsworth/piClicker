# Links
   * http://www.ericescobar.com/wordpress/raspberry-pi-3-wireless-hacking-platform-wifipi/

# Todo
* C&C for pi

# Install Instructions
* If you don't have access, setup a gitlab account and give shollingsworth@barracuda.com your username to add to project
* To give the pi network access run:
    * `./setup_pi_to_interwebs.sh` 
    * this will ask for some wireless input information
* Install Git after the reboot:
    * `apt -y install git`

## Authenticated Repo Access (it's private for now, you have (2) options)

### SSH key on PI
* Instructions: https://docs.gitlab.com/ee/gitlab-basics/create-your-ssh-keys.html
* Generate SSH key on pi run the cmd:
    * `ssh-keygen`
    * `git clone git@gitlab.com:shollingsworth/piClicker.git`

### User Access Token (can have expire date)
* Instructions: https://docs.gitlab.com/ce/user/profile/personal_access_tokens.html#creating-a-personal-access-token
* run the cmd to clone after you setup / and import your public key
    * `user=shollingsworth; token='*******************'`
    * git clone `https://${user}:${token}@gitlab.com/shollingsworth/piClicker.git`

## Install
* Assuming you have internet, run the following cmd
    * `./setup.sh mypiclicker.localhost`
* To secure ssh as well
    * `./setup.sh mypiclicker.localhost --ssh`

## Running the program
* `./wireless_scan.py <adapter>(wlan1) <bssid>00:00:00:00:00:00`

# Demos
## Clicker
* Run clicker program initially. First arg is how long your want it to run, 2nd is the initial click frequency
    * ./demo_clicking.sh 60 100

## Sending signals to clicker
* Adjust the click frequency dynmaically by running commands like so (in order of clicking intensity)
    * `./demo_signal_clicking.sh 1000` 
        * 1 second / 1000 ms
    * `./demo_signal_clicking.sh 700`
        * .700 seconds / 700 ms
    * `./demo_signal_clicking.sh 500`
        * see above you can figure it out
    * `./demo_signal_clicking.sh 200`
        * ...
    * `./demo_signal_clicking.sh 100`
        * ...
    * `./demo_signal_clicking.sh 30`
        * ...
    * `./demo_signal_clicking.sh 0`
        * This will play the static sound
    * `./demo_signal_clicking.sh -1`
        * This will play the error sound
