#TODO try AppendMarkup
#TODO try Annotation - check the wire to see the annotation system if you want to do this
# look at http://code.google.com/p/google-wave-resources/source/browse/trunk/samples/extensions/robots/python/syntaxy/syntaxy.py
# for annotation use blip.SetAnnotation
# look at http://code.google.com/p/downy/source/browse/downy.py?r=39a14157d5a7294ceee5bd1027b1b82c25dfceb3
# look at http://code.google.com/p/msg-in-a-bottle-wave-robot/source/browse/trunk/miab.py for storing info on a wave

from waveapi import events
from waveapi import model
from waveapi import robot
from waveapi import document
import re
import logging

logger = logging.getLogger('janey-robot')
logger.setLevel(logging.DEBUG)

current_version = '1.19'

def GetResponseForCommand(command):
    if command == 'help':
        response = "\n\n I'll give you some help in a moment"
    else:
        response = "Hmm, I'm not sure what you mean, sorry!"
    return response

def OnParticipantsChanged(properties, context):
    """Invoked when any participants have been added/removed."""
    added = properties['participantsAdded']
    #for p in added:
    #    Notify(context)

def OnRobotAdded(properties, context):
    """Invoked when the robot has been added."""
    root_wavelet = context.GetRootWavelet()
    root_wavelet.CreateBlip().GetDocument().SetText("Hi, I'm janey-robot, let me help you find journals, I'm version " + current_version)

def Notify(context):
    root_wavelet = context.GetRootWavelet()
    root_wavelet.CreateBlip().GetDocument().SetText("Hi everybody!")
 
def OnBlipSubmitted(properties, context):
    """Invoked when a blip has been added."""
    blip = context.GetBlipById(properties['blipId']) 
    blip_text_view = blip.GetDocument()

    # regex generated using http://txt2re.com/index-python.php3?s=aasfd%20(janey:command)%20aslfkjasf&4&-7&-44&-42&-43
    re1='.*?'	# Non-greedy match on filler
    re2='(\\()'	# Any Single Character 1
    re3='(janey)'	# Word 1
    re4='(:)'	# Any Single Character 2
    re5='((?:[a-z][a-z]+))'	# Word 2
    re6='(\\))'	# Any Single Character 3
    rg = re.compile(re1+re2+re3+re4+re5+re6,re.IGNORECASE|re.DOTALL)
    m = rg.search(blip_text_view.GetText())

    if m:
        command=m.group(4)
        response = GetResponseForCommand(command)
        blip_text_view.AppendText(response)
        logger.debug('message was %s' % response)

if __name__ == '__main__':
    logger.debug('text: %s' % "running version " + current_version)
    myRobot = robot.Robot('janey-robot', 
            image_url='http://janey-robot.appspot.com/assets/icon.png',
            version=current_version,
            profile_url='http://janey-robot.appspot.com/')
    #myRobot.RegisterHandler(events.WAVELET_PARTICIPANTS_CHANGED, OnParticipantsChanged)
    myRobot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)
    myRobot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
    myRobot.Run()