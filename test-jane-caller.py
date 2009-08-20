from xml.dom import minidom
import urllib
from BeautifulSoup import BeautifulStoneSoup

class journalInfo:
    def __init__(self, name):
        self.journalname =  name
        self.rank = 0
        self.score = 0

class authorInfo:
    def __init__(self, name):
        self.name =  name
        self.rank = 0
        self.score = 0
        self.articles = []

class articleInfo:
    def __init__(self, pmid):
        self.pmid = pmid
        self.title = ""
        self.rank = 0
        self.score = 0
        
def sort_results_by_rank(i,j):
    """
    all root objects returned in the jane xml tree have a rank
    and score attribute, this is a custom sort on rank
    """
    #print "in rank sorting"
    if i.rank > j.rank:
        return 1
    elif j.rank == i.rank:
        return 0
    else: # j.rank > i.rank
        return -1

def sort_results_by_score(i,j):
    """
    all root objects returned in the jane xml tree have a rank
    and score attribute, this is a custom sort on score
    """

    if i.score > j.score:
        return 1
    elif j.score == i.score:
        return 0
    else: # j.rank > i.rank
        return -1

def GetJournalInfo(soup):
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

    tags = [tag for tag in soup.results.findAll(recursive=False)]
    author_metric = tags[0::3]
    author_names = tags[1::3]
    author_evidence = tags[2::3]
    
    #print author_metric
    
    #print author_names
    #print author_evidence
    
    return_results = []
    for metric, name, evidence in zip (author_metric, author_names, author_evidence):
        #print metric, name, evidence
        
        rank = metric['rank']
        score = metric['score']
        name = name.contents[0]
        author_articles = GetArticleInfo(evidence)
        evidence = evidence
         
        au = authorInfo(name)
        au.score = int(score) # read as str, convert to int for sorting
        au.rank = int(rank) # read as str, convert to int for sorting
        au.articles = author_articles
         
        return_results.append(au)
    return return_results

def formatJournalResults(journal_results):
    """
    take journalname rank and score and format for printing
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
    
def genPubMedLinkFromPMID(pmid):
    return "http://www.ncbi.nlm.nih.gov/pubmed/" + pmid

def formatArticleResults(Results):
    """
    take article title  rank and score and format for printing
    include pmid and generate a link to pubmed
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
    print query_url

    try:
        html = urllib.urlopen(query_url)
        document = html.read()
    except:
        # add error loggin here
        return "oops, there was a problem calling the JANE service, sorry!"
    try:
        vanilla_doc = document.decode('us-ascii', 'ignore')
        soup = BeautifulStoneSoup(vanilla_doc)
    except:
        # add error loggin here
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

def process_query(command,query_text):
    result = QueryJaneAPI(command,query_text)
    print result
        
query_text = "zebra fish cancer"
# commands = ["journals","authors","articles"]
commands = ["authors"]

for command in commands:
    print command
    process_query(command, query_text)