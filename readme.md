# How to use DCI-Hook
### Welcome!
This is a discord web hook for marching band enthusiasts to use that want to keep up with scores for the current and future Drum Corps International (DCI) seasons

### How it works?
Scores are webscraped from dci.org and posted as tabular message embed into a discord text channel.  No need to worry about hosting unless you would like to copy the source code and modify to your liking.  This hook is hosted on AWS as a Lambda Function and will be triggered daily roughly for the entire Drum Corps season.  

All the dirty work has been handled!

### How to use?
Create your text channel that you want the hook to post to, edit the channel settings, and create a webhook underneath the integrations tab!  From there, provide the webhook URL and then you're all set - the hook will start posting scores when the time comes! 

#### Prerequisites
1. Have Python 3.x installed - https://www.python.org/downloads/
2. Have latest version of docker desktop - https://www.docker.com/products/docker-desktop/
3. Have pip installed - https://pip.pypa.io/en/stable/installation/#

#### Local Testing
Steps:
1. Clone this repo `git clone https://github.com/MKanarr/DCI-Scores.git`
2. Create virtual env `python3 -m venv <your-env-name>`
3. Active virtual env `source <your-env-name>/bin/activate`
4. Run `pip3 install -r requirements.txt`
5. Create/Update `.env`
    * Sample
        ```bash
        TEST_HOOK_URL=<discord-web-hook-url>
        DYNAMO_SHOW_TABLE_LOCAL=<local-table-name>
        # used to webscrape scores
        SCORE_URL=https://www.dci.org/score/final-scores/
        ```
6. Run `docker compose up` in another terminal window
    * Docker daemon must be running
7. Run `python3 dci-hook-local.py`