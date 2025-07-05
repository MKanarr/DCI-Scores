# How to use DCI-Hook
### Welcome!
This is a discord web hook for marching band enthusiasts to use that want to keep up with scores for the current and future Drum Corps International (DCI) seasons

### How it works?
Scores are webscraped from dci.org and posted as tabular message embed into a discord text channel.  No need to worry about hosting unless you would like to copy the source code and modify to your liking.  This hook is hosted on AWS as a Lambda Function and will be triggered daily roughly for the entire Drum Corps season.  

All the dirty work has been handled!

### How to use?
Create your text channel that you want the hook to post to, edit the channel settings, and create a webhook underneath the integrations tab!  From there, provide the webhook URL and then you're all set - the hook will start posting scores when the time comes! 