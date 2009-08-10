#TODO try AppendMarkup
#TODO try Annotation
#  check the wire to see the annotation system if you want to do this
# look at http://code.google.com/p/google-wave-resources/source/browse/trunk/samples/extensions/robots/python/syntaxy/syntaxy.py
# for annotation use blip.SetAnnotation
# look at http://code.google.com/p/downy/source/browse/downy.py?r=39a14157d5a7294ceee5bd1027b1b82c25dfceb3
# look at http://code.google.com/p/msg-in-a-bottle-wave-robot/source/browse/trunk/miab.py for storing info on a wave

from waveapi import events
#from waveapi import model
from waveapi import robot
#from waveapi import document
import re
import logging
from xml.dom import minidom
import urllib

logger = logging.getLogger('janey-robot')
logger.setLevel(logging.DEBUG)

current_version = '1.1.33'
HELP_MESSAGE = "\n\n I'll give you some help in a moment"

def OnRobotAdded(properties, context):
    """
    Invoked when the robot has been added.
    """
    HELLO_MESSAGE = "Hi, I'm janey-robot, let me help you find journals, \
                        I'm version " + current_version
    root_wavelet = context.GetRootWavelet()
    root_wavelet.CreateBlip().GetDocument().SetText(HELLO_MESSAGE)

def Notify(context):
    """
    We will only notify when the robot is added or updated, not 
    when a new participant is added, this increases clutter in the wave
       
    """
    root_wavelet = context.GetRootWavelet()
    root_wavelet.CreateBlip().GetDocument().SetText("Hi everybody!")

def StripCommandFromBlipText(blipText, command):
    """
    returns the blip text with the command text removed
    this function is also used to return the query string to be passed to JANE

    """
    replace_string = "(janey:" + command + ")"
    stripped_text = blipText.replace(replace_string,"")
    return stripped_text

def StripCommandFromBlip(properties, context, blip_text, command):
    """
    Take a blip and modify the blip in place
    Remove the janey command string from the blip

    """
    logger.debug('stripping the command from the blip')    
    blip = context.GetBlipById(properties['blipId'])
    stripped_text = StripCommandFromBlipText(blip_text, command)
    blip.GetDocument().SetText(stripped_text)

def QueryJaneAPI(command, query_text):
    """
    uses http GET
    
    The 3 relevant URLs are
    http://biosemantics.org:8080/jane/journals
    http://biosemantics.org:8080/jane/authors
    http://biosemantics.org:8080/jane/articles

    These accept GET and POST requests with the following parameters:

    text The text you want to search with
    count The number of articles to show (articles only)
    offset The offset of the list (articles only)

    For example:
    http://biosemantics.org:8080/jane/journals?text=malaria%20vaccines

    """
    logger.debug('generating JANE API call URI')    
    jane_root_url = 'http://biosemantics.org:8080/jane/'
    encoded_query_text = urllib.urlencode({'text':query_text})
    query_url = jane_root_url + command + "/" + encoded_query_text
    logger.debug(query_url)
    #xml = minidom.parse(urllib.urlopen(query_url))
    #journals = xml.getElementsByTagName('journalname')
    #journal_names = "\n".join(journals)
    return query_url

def ReplyToBlipWithJaneInfo(properties, context, blip_text, command):
    """
    If we recognize the command, send a query to the Jane API
    If not demur with a polite response

    """
    if command == 'help':
        response = HELP_MESSAGE
    elif command in ['authors', 'journals', 'articles']:
        query_text = StripCommandFromBlipText(blip_text, command)
        logger.debug('about to call JANE API')    
        query_result = QueryJaneAPI(command, query_text)
        response = "The " + command + " I would suggest are: \n" + query_result
    else:
        response = "Hmm, I'm not sure what you mean, sorry!,\
         try (janey:help) for a list of commands I understand"
        
    blip = context.GetBlipById(properties['blipId']) 
    blip.CreateChild().GetDocument().SetText(response)
    
def OnBlipSubmitted(properties, context):
    """
    Invoked when a blip has been added.
    """
    blip = context.GetBlipById(properties['blipId']) 
    blip_text_view = blip.GetDocument()
    blip_text = blip_text_view.GetText()

    # regex generated using http://txt2re.com/index-python.php3?s=aasfd%20(janey:command)%20aslfkjasf&4&-7&-44&-42&-43
    re1 = '.*?'	# Non-greedy match on filler
    re2 = '(\\()'	# Any Single Character 1
    re3 = '(janey)'	# Word 1
    re4 = '(:)'	# Any Single Character 2
    re5 = '((?:[a-z][a-z]+))'	# Word 2
    re6 = '(\\))'	# Any Single Character 3
    rg = re.compile(re1+re2+re3+re4+re5+re6, re.IGNORECASE|re.DOTALL)
    logger.debug('about to search blip text')    
    m = rg.search(blip_text)

    if m:
        command = m.group(4)
        StripCommandFromBlip(properties, context, blip_text, command)
        ReplyToBlipWithJaneInfo(properties, context, blip_text, command)
        logger.debug('query syntax recognised, command was %s', command)

if __name__ == '__main__':
    logger.debug('text: %s' % "running version " + current_version)
    myRobot = robot.Robot('janey-robot', 
            image_url='http://janey-robot.appspot.com/assets/icon.png',
            version=current_version,
            profile_url='http://janey-robot.appspot.com/')
    myRobot.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)
    myRobot.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
    myRobot.Run()