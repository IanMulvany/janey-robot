import re
import logging
import urllib
from BeautifulSoup import BeautifulStoneSoup
from networkx import *

logger = logging.getLogger('janey-robot')
logger.setLevel(logging.DEBUG)

current_version = '2.2'
HELP_MESSAGE = "I query http://www.biosemantics.org/jane/, my commands are:  \
                   (janey:journals) - returns a list of recommended journals\n \
                   (janey:articles) - returns a list of related articles\n \
                   (janey:authors) - returns a list of related authors\n \
                   (janey:about) - gives a little info about me\n \
                   (janey:graph) - mini co-authorship network\n \
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
        self.year = 0
        self.authors = []
        
        
def sort_results_by_rank(i, j):
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


def sort_results_by_score(i, j):
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


def sort_results_by_year(i, j):
    """
    Article objects have a year attribute. This is the year that they were published.
    This custom sort, sorts articles by year, yeahh!

    """
    if i.year > j.year:
        return 1
    elif j.year == i.year:
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
        year = article.year.contents[0]
        author_tags = article.findAll('author')
        author_names = [tag.contents[0] for tag in author_tags]
        # add the info into our article info class object
        a = articleInfo(pmid)
        a.score = int(score) # read as str, convert to int for sorting
        a.rank = int(rank) # read as str, convert to int for sorting
        a.title = title
        a.year = int(year) # read as str, convert to int for sorting
        a.authors = author_names
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


def genLink(a, b):
    return '"' + a.pmid + " " + str(a.year) + '" -> "' + b.pmid + " " + str(b.year) + '"\n'
    #return a.pmid + " -> " + b.pmid + "\n"


def graphArticleRelationships(Results):
    """
    Take the rank and score and format for printing.
    Picking the top 5 is arbitrary. If less than 5 results are 
    returned by the API this module will break.
    
    TODO: factor out the number of results that are returned.

    """    
    Results.sort(sort_results_by_year)
    text = "#!dot\n" # required for graph robot
    targets = Results
    max_links = 12 # artifical limit to fit in demo window
    link_num = 0 
    for a in Results:
        a_auths = a.authors
        targets.remove(a) # if a -> b, then b -> a, so don't check twice
        for b in targets:
            b_auths = b.authors
            for a_auth in a_auths:
                if a_auth in b_auths and link_num < max_links:
                    edge = genLink(a, b)
                    text = text + edge
                    link_num = link_num + 1
                    break
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


def generateQueryUrl(command, query_text):
    """
    If the command is to graph, then we pull more results in order to find
    an overlap between authors.
    
    """
    jane_root_url = 'http://biosemantics.org:8080/jane/'
    encoded_query_text = urllib.quote(query_text.rstrip().lstrip())
    if command == 'graph':
        query_url = jane_root_url + "articles?text=" + encoded_query_text
        query_url = query_url + "&count=100"
    else:
        query_url = jane_root_url + command + "?text=" + encoded_query_text
            
    print query_url
    return query_url
    
    
def downloadXMLFromnJane(query_url):
    """
    TODO: convert to a POST call rather than a GET call 
    TODO: create a propoer user agent so JANE recognises the calls as coming from janey
    TODO: add proper error handling to this botched script
    
    """
    try:
        html = urllib.urlopen(query_url)
        document = html.read()
        vanilla_doc = document.decode('us-ascii', 'ignore')
        soup = BeautifulStoneSoup(vanilla_doc)
    except:
        return FALSE
    return soup

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
    query_url = generateQueryUrl(command, query_text)
    soup = downloadXMLFromnJane(query_url)
    
    if not soup:
        return "error in communicating with JANE server"
    
    return_text = ""
    if command == "journals":
        journal_results = GetJournalInfo(soup)
        return_text = formatJournalResults(journal_results)
    elif command == "authors":
        author_results = GetAuthorInfo(soup)
        return_text = formatAuthorResults(author_results)
    elif command == "articles":
        article_results = GetArticleInfo(soup)
        #return_text = formatArticleResults(article_results)
        return_text = graphArticleRelationships(article_results)
    elif command == "graph":
        article_results = GetArticleInfo(soup)
        #return_text = formatArticleResults(article_results)
        return_text = graphArticleRelationships(article_results)                 
    return return_text



query_text = "H1N1 china mortality"
command = "graph"
query_result = QueryJaneAPI(command, query_text)
print query_result    
