# cecmonitor <a href="https://hub.docker.com/r/negativefusion/cecmonitor/"><img src="https://img.shields.io/docker/pulls/negativefusion/cecmonitor.svg?style=flat-square&logo=docker" alt="Docker Pulls"></a>
Monitor CEC HDMI over the network to catch standby command and send power off to Android TV thru adb shell

Turns off an Android TV using adb shell commands. Not all Android TVs respect the HDMI "standby" 
command (even if the HDMI-CEC settings are enabled) and as result, the won't turn off automatically when a 
standby broadcast message is sent via HDMI. 

This package aims to solve that using `adb` (Android Debug Bridge). When a broadcast 
standby command has been sent, this program sends an adb shell command to turn off the TV using adb shell.

### Android TV Setup

Turn on your Android TV "Developer Mode" and enable adb debug logging.

Used https://github.com/paulsaccount/hdmi_cec_to_adb as a basis and inspired me to create my version
