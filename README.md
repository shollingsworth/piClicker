# Presentation
[Defcon 26 Slides](./docs/piClicker_presentation_dc26_2018_08_10.odp)

# Command and Control w/ Slack
* You'll need an AWS account, an will need to create an access id and secret
[See WCTF Slack Bot Repo](https://github.com/shollingsworth/wctf-slack-bot/blob/master/README.md)

# Running daemon in a DEV environment
## Clone repo

```
git clone git@github.com:shollingsworth/piClicker.git
cd piClicker
make venv
source ./venv/bin/activate
pip install ./dist/piClicker-2.0.1.tar.gz
cd ./src/piclicker
```

## run control and navigate to UI
* `./control.py`
* naviagate to http://127.0.0.1:5000 to see UI

# Links
* [Todo](./TODO.md)
