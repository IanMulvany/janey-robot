from waveapi import events
from waveapi import robot
import re
import logging
import urllib
from BeautifulSoup import BeautifulStoneSoup

logger = logging.getLogger('janey-robot')
logger.setLevel(logging.DEBUG)

current_version = '2.1'
HELP_MESSAGE = "I query http://www.biosemantics.org/jane/, my commands are:  \
                   (janey:journals) - returns a list of recommended journals\n \
                   (janey:articles) - returns a list of related articles\n \
                   (janey:authors) - returns a list of related authors\n \
                   (janey:about) - gives a little info about me\n \
                   (janey:help) - prints this message"       
ABOUT_MESSAGE = "I pass the content of the blip I am called from to the \
Journal Name Author Estimator service, and I put some of the \
response from that service into a reply blip. \
You can get more info about the nice JANE people \
at\n\n \
http://www.biosemantics.org/jane/faq.php.\n\n \
You can interact directly with their service at: \
\nhttp://www.biosemantics.org/jane/\n\n \
I was written by Ian Mulvany from Nature Publishing Group as a \
proof of concept for the ScienceOnline London Conference, 2009.\n\n \
You can invite him to your wave at ianmulvany@wavesandbox.com \n\n \
My source code can be found at:\n\n \
http://github.com/IanMulvany/janey-robot/tree/master\n\n \
For help on my commands type (janey:help)"


class journalInfo:
    """"
    Models partial journal information.

    """    
    def __init__(self, name):
        self.journalname =  name
        self.rank = 0
        self.score = 0


class authorInfo:
    """"
    Models partial author information.
    articles is an empty list, it will store articleInfo class objects,
    possibly better to inherit this?

    """    
    def __init__(self, name):
        self.name =  name
        self.rank = 0
        self.score = 0
        self.articles = []


class articleInfo:
    """
    Models partial article information

    """    
    def __init__(self, pmid):
        self.pmid = pmid
        self.title = ""
        self.rank = 0
        self.score = 0
        
        
def sort_results_by_rank(i,j):
    """
    All root objects returned in the jane xml tree have a rank
    and score attribute, this is a custom sort on rank.

    """
    if i.rank > j.rank:
        return 1
    elif j.rank == i.rank:
        return 0
    else: # j.rank > i.rank
        return -1


def sort_results_by_score(i,j):
    """
    All root objects returned in the jane xml tree have a rank
    and score attribute, this is a custom sort on score

    """
    if i.score > j.score:
        return 1
    elif j.score == i.score:
        return 0
    else: # j.rank > i.rank
        return -1


def genPubMedLinkFromPMID(pmid):
    return "http://www.ncbi.nlm.nih.gov/pubmed/" + pmid


def GetJournalInfo(soup):
	"""
	Parses the returned xml from JANE and extracts some information about
	journals.
	
	"""
    journals = soup.findAll('journal')
    return_results = []
    for journal in journals:
        title = journal.journalname.contents[0]
        rank = journal['rank']
        score = journal['score']
        j = journalInfo(title)
        j.score = int(score) # read as str, convert to int for sorting
        j.rank = int(rank) # read as str, convert to int for sorting
        return_results.append(j)
    return return_results


def GetArticleInfo(soup):
	"""
	Parses the returned xml from JANE and extracts some information about
	articles.
	
	"""
    articles = soup.findAll('article')
    return_results = []
    for article in articles:
        # extract the info from the xml tree
        title = article.title.contents[0]
        rank = article['rank']
        score = article['score']
        pmid = article.pmid.contents[0]
        # add the info into our article info class object
        a = articleInfo(pmid)
        a.score = int(score) # read as str, convert to int for sorting
        a.rank = int(rank) # read as str, convert to int for sorting
        a.title = title
        return_results.append(a)
    return return_results


def GetAuthorInfo(soup):
	"""
	Parses the returned xml from JANE and extracts some information about
	authors.
	
	The author nodes are non-trivial, each author includes an evidence node, inside
	of which tere are article nodes, indide of which there are author nodes, but 
	only author nodes containing author names.
	
	"""
    tags = [tag for tag in soup.results.findAll(recursive=False)]
    author_metric = tags[0::3]
    author_names = tags[1::3]
    author_evidence = tags[2::3]
    
    return_results = []
    for metric, name, evidence in zip (author_metric, author_names, author_evidence):
        rank = metric['rank']
        score = metric['score']
        name = name.contents[0]
        author_articles = GetArticleInfo(evidence)
        evidence = evidence
        # add the info into our article info class object
        au = authorInfo(name)
        au.score = int(score) # read as str, convert to int for sorting
        au.rank = int(rank) # read as str, convert to int for sorting
        au.articles = author_articles    
        return_results.append(au)
    return return_results

def formatJournalResults(journal_results):
    """
    Take the rank and score and format for printing.
	Picking the top 5 is arbitrary. If less than 5 results are 
	returned by the API this module will break.
	
	TODO: factor out the number of results that are returned.

    """
    journal_results.sort(sort_results_by_rank)
    top_5_by_rank = journal_results[0:5]
    journal_results.sort(sort_results_by_score)
    top_5_by_score = journal_results[0:5]

    text = "top 5 journals by score: "
    for journal in top_5_by_score:
        text = text + journal.journalname  + " " +  str(journal.score) + "\n"
    
    text = text + "\ntop 5 journals by rank: \n"
    for journal in top_5_by_rank:
        text = text + journal.journalname + " " + str(journal.rank) + "\n"      
    return text


def formatArticleResults(Results):
    """
    Take the rank and score and format for printing.
	Picking the top 5 is arbitrary. If less than 5 results are 
	returned by the API this module will break.
	
	TODO: factor out the number of results that are returned.

    """    
    Results.sort(sort_results_by_rank)
    top_5_by_rank = Results[0:5]
    Results.sort(sort_results_by_score)
    top_5_by_score = Results[0:5]
    
    text = "top 5 articles by score: "
    for article in top_5_by_score:
        text = text + article.title + " " +  str(article.score) + "\n"
        pubmed_link = genPubMedLinkFromPMID(article.pmid)
        text = text + article.pmid + "(" + pubmed_link + ")\n"
    
    text = text + "\ntop 5 articles by rank: \n"
    for article in top_5_by_rank:
        text = text + article.title + " " + str(article.rank) + "\n"
        pubmed_link = genPubMedLinkFromPMID(article.pmid)
        text = text + article.pmid + "(" + pubmed_link + ")\n"                    
    return text


def formatAuthorResults(Results):
    """
    Take the rank and score and format for printing.
	Picking the top 5 is arbitrary. If less than 5 results are 
	returned by the API this module will break.
	
	TODO: factor out the number of results that are returned.

    """
    Results.sort(sort_results_by_rank)
    top_5_by_rank = Results[0:5]
    Results.sort(sort_results_by_score)
    top_5_by_score = Results[0:5]

    text = "top 5 authors by score: "
    for author in top_5_by_score:
        text = text + author.name + " " +  str(author.score) + "\n"
    
    text = text + "\ntop 5 authors by rank: \n"
    for author in top_5_by_rank:
        text = text + author.name + " " + str(author.rank) + "\n"
    
    return text


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
    jane_root_url = 'http://biosemantics.org:8080/jane/'
    encoded_query_text = urllib.quote(query_text.rstrip().lstrip())
    query_url = jane_root_url + command + "?text=" + encoded_query_text
    try:
        html = urllib.urlopen(query_url)
        document = html.read()
    except:
        return "oops, there was a problem calling the JANE service, sorry!"
    try:
        vanilla_doc = document.decode('us-ascii', 'ignore')
        soup = BeautifulStoneSoup(vanilla_doc)
    except:
        return "oops, I chocked trying to process the returned xml, sorry!"
    
    return_text = ""
    if command == "journals":
        journal_results = GetJournalInfo(soup)
        return_text = formatJournalResults(journal_results)
    elif command == "authors":
        author_results = GetAuthorInfo(soup)
        return_text = formatAuthorResults(author_results)
    elif command == "articles":
        article_results = GetArticleInfo(soup)
        return_text = formatArticleResults(article_results)
                 
    return return_text


def OnRobotAdded(properties, context):
    """
    Invoked when the robot has been added.

    """
    HELLO_MESSAGE = "Hi, I'm janey-robot, let me help you find journals. For help type (janey:help) \
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


def ReplyToBlipWithJaneInfo(properties, context, blip_text, command):
    """
    If we recognize the command, send a query to the Jane API
    If not demur with a polite response

    """
    if command == 'help':
        response = HELP_MESSAGE
    elif command == 'about':
        response = ABOUT_MESSAGE
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