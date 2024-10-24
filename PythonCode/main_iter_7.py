import openai
import time
from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import tldextract
import re
from openpyxl import load_workbook
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import transformers
import tiktoken
import openpyxl
import traceback
import math
import trafilatura
import json
from googlesearch import search
from sentence_transformers import SentenceTransformer, util
from SentenceSplitter import split_into_sentences
from urllib.parse import urlparse
from nltk.tokenize import sent_tokenize
from multiprocessing import Process, Manager
import ast
import psutil
import sys
from difflib import SequenceMatcher



knownLinkTrust = {}

processes = []
#Sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
factcheckdata = 0

startTime = time.time()

app = Flask(__name__)
CORS(app)

trustList = ['Center', 'Right-Center', 'Left-Center', 'Pro-Science']

excel_file = "WebsiteCategoriesModified.xlsx"
df = pd.read_excel(excel_file)

socialMediaSites = ['quora.com', 'reddit.com', 'youtube.com', 'tiktok.com', 'instagram.com', 'twitter.com', 'pinterest.com', 'twitch.com', 'facebook.com', 'amazon.com', 'fandom.com']

websiteList = df['Website'].tolist()
websiteTrustMeasureList = df['Status'].tolist()

cleanWebsiteList = []

genai.configure(api_key="[insert gemini api key]")

model2 = genai.GenerativeModel('gemini-pro')

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
            AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}



for i in websiteList:
    if '(' in i:
        a = i[i.find("(") + 1:i.find(")")]
        if "www." in a:
            a = a.replace("www.", '')
        if "https://" in a:
            a = a.replace("https://", '')
        if "http://" in a:
            a = a.replace("http://", '')
        a = a.lower()
        a = tldextract.extract(a).domain + '.' + tldextract.extract(a).suffix
        cleanWebsiteList.append(a)
    else:
        i = i.lower()
        try:
            i = tldextract.extract(i).domain + '.' + tldextract.extract(i).suffix
        except:
            pass
        cleanWebsiteList.append(i)

websiteTrust = dict(zip(cleanWebsiteList, websiteTrustMeasureList))

#print("Website List Processed and Cleaned")
openai.api_key = "[insert chatgpt api key]"

encoding_token_counter = tiktoken.encoding_for_model("gpt-4-0125-preview")

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def countToken(text):
    token_count = len(encoding_token_counter.encode(text))
    return token_count

def getColumnExcelFile(filePath, columnNumber, excludeFirstValue):
    book = load_workbook(filePath)
    sheet = book.active

    count = 0
    totalColumn = 10
    columnList = []

    for row in sheet:
        for cell in row:
            if cell.value is not None:
                count += 1
            if count == columnNumber:
                columnList.append(cell.value)
            if count == totalColumn:
                count = 0
    if excludeFirstValue:
        columnList = columnList[1:40]
        return columnList
    else:
        return columnList

def sentenceSimilarity(query, text, website):
    # Gets the dot products of query and text
    sentences = [query] + split_into_sentences(text)
    sentence_embeddings = model.encode(sentences)

    sentence_dotproducts = []
    for i in sentence_embeddings:
        sentence_dotproducts.append(float(util.dot_score(sentence_embeddings[0], i)[0][0]))
    sentence_dotproduct_website_array = []
    for sentence, dotproduct in zip(sentences, sentence_dotproducts):
        sentence_dotproduct_website_array.append([sentence, dotproduct, website])
    sentence_dotproduct_website_array.pop(0)
    sentence_dotproduct_website_array = sorted(sentence_dotproduct_website_array, key=lambda x: x[1], reverse=True)
    sentences.pop(0)
    return sentence_dotproduct_website_array, sentences

def cleanUrl(url):
    # print("url: " + url)
    try:
        url = tldextract.extract(url).domain + '.' + tldextract.extract(url).suffix
    except:
        pass
        # print("url aint working bois")
    if "www." in url:
        url = url.replace("www.", '')
    if "https://" in url:
        url = url.replace("https://", '')
    if "http://" in url:
        url = url.replace("http://", '')
    return url

def parseGPTJSON(parseGPTResponse, length):
    recordString = False
    string_a = ""
    string_list = []
    count = 0
    doubleString = False
    if parseGPTResponse.find("\"") != -1 and (parseGPTResponse.find("\'") == -1 or parseGPTResponse.find("\"") < parseGPTResponse.find("\'")):
        doubleString = True
    for i in parseGPTResponse:
        if recordString:
            string_a += i
        if (i == "\"" and recordString == False and doubleString) or (i == "\'" and recordString == False and doubleString == False):
            recordString = True
            # print("RECORDING STUFF")
        elif (i == "\"" and recordString == True and doubleString) or (i == "\'" and recordString == True and doubleString == False):
            # print("APPENDING STUFF")
            recordString = False
            string_a = string_a[:-1]
            string_list.append(string_a)
            string_a = ""
        count += 1
    secondList = []
    # print(string_list)
    for i in string_list:
        # print(i.count(" "))
        # print(length)
        if i.count(" ") > length:
            secondList.append(i)
    return secondList

def SearchOnGoogle(query, url):
    websites = []
    domain = [cleanUrl(url)]
    print("searching up: " + query)
    searchResultsContent = []
    searched = False
    while not searched:
        try:
            for i in search(query, tld="co.in", num=15, stop=15):
                websites.append(i)
            searched = True
        except:
            print(traceback.format_exc())
            print("sleeping cuz i can't google bro!")
            time.sleep(10)
    #print(websites)
    finalWebsites = []
    for i in websites:
        #print("startLoop")
        content = extractMainContent(i)
        #print("ExtractedMainContent")
        alreadyUsed = False
        for j in finalWebsites:
            if similar(i, j) >= 0.8:
                alreadyUsed = True
        if not alreadyUsed:
            if i in knownLinkTrust:
                #print("Website is known to be trusted or not")
                if knownLinkTrust[i] == "trusted":
                    searchResultsContent.append(content)
                    finalWebsites.append(i)
                    #print(i + " trusted through experience")
                elif knownLinkTrust[i] == "not_trusted":
                    #print(i + " excluded through experience")
                    pass
            else:
                #print("Manual website check")
                if cleanUrl(i) in socialMediaSites or cleanUrl(i) in domain or content is None:
                    #print(i + " excluded through fast route")
                    knownLinkTrust[i] = "not_trusted"
                else:
                    #print("beforeTry")
                    try:
                        #print("Trying")
                        if websiteStatus(cleanUrl(i)) in trustList:
                            finalWebsites.append(i)
                            domain.append(urlparse(str(i)).netloc)
                            if cleanUrl(i) == 'wikipedia.org':
                                content = extractWikiContent(content)
                            else:
                                content = content.replace('\\n', ' ')
                            searchResultsContent.append(content)
                            #print(i + " trusted through database")
                            knownLinkTrust[i] = "trusted"
                        else:
                            #print(i + " excluded through database")
                            knownLinkTrust[i] = "not_trusted"
                    except:
                        #print("Doesn't exist in database")
                        if cleanUrl(i) not in socialMediaSites and cleanUrl(i) not in domain and content is not None:
                            #print("Checking if website reliable")
                            if checkIfWebsiteReliable(cleanUrl(i)):
                                #print("done checking, it is reliable")
                                finalWebsites.append(i)
                                domain.append(urlparse(str(i)).netloc)
                                if cleanUrl(i) == 'wikipedia.org':
                                    content = extractWikiContent(content)
                                else:
                                    content = content.replace('\\n', ' ')
                                searchResultsContent.append(content)
                                content = content.replace('\\n', ' ')
                                searchResultsContent.append(content)
                                #print(i + " trusted through google+chatGPT")
                                knownLinkTrust[i] = "trusted"
                        else:
                            #print(i + " excluded through database")
                            knownLinkTrust[i] = "not_trusted"
            if len(finalWebsites) >= 3:
                break

    # for i in finalWebsites:
    #     content = extractMainContent(i)
    #     if cleanUrl(i) not in domain and content is not None:
    #         realFinalWebsites.append(i)
    #         domain.append(urlparse(str(i)).netloc)
    #         searchResultsContent.append(content)
    print(finalWebsites)
    if len(searchResultsContent) > 3:
        searchResultsContent = searchResultsContent[slice(3)]
        finalWebsites = finalWebsites[slice(3)]
    website_content_array = []
    for website, content in zip(finalWebsites, searchResultsContent):
        website_content_array.append([website, content, query])
    #print("finished searching up: " + query)
    #print(website_content_array)
    return website_content_array

def turnIntoDictionary(string):
    string = list(string)
    for i in range(len(string)):
        if string[i] == "“" or string[i] == "”":
            if i != (len(string) - 1) and string[i+1] == ":":
                string[i] = "\""
            if i != 0 and string[i-1] == ":":
                string[i] = "\""

    string = "".join(string)
    string.replace("\n", "\\n")
    # function above replaces all “ with a " because python can't recognize that type of double quote
    start = 0
    end = 0
    for i in range(len(string)):
        if string[i] == "{":
            start = i
        if string[i] == "}":
            end = i
    croppedString = string[start:end+1]
    return ast.literal_eval(croppedString)

def extractMainContent(url):
    #print("start fetch")
    downloaded = trafilatura.fetch_url(url)
    #print("done fetch")
    return trafilatura.extract(downloaded)

def extractWikiContent(content):
    lines = content.split("\n")
    count = 0
    noSource = []
    for line in lines:
        if line.strip().startswith('-') and "References" in lines[count-1]:
            break
        count += 1
        noSource.append(line)
    noSource = ' '.join(noSource)

    pattern = re.compile(r'\[\d+\]')

    noSource = re.sub(pattern, '', noSource)

    return noSource

def AskChatGPT(question):
    receivedAnswer = False
    response = ""
    while not receivedAnswer:
        try:
            chat_completion = openai.ChatCompletion.create(model="gpt-4-turbo-preview",
                                                                   messages=[{"role": "user", "content": question}],
                                                                   response_format={"type": "json_object"}
                                                                   )
            response = chat_completion["choices"][0]["message"]["content"]
            print("chatgpt response: ")
            print(response)
            receivedAnswer = True
        except:
            print(traceback.format_exc())
            print("sleeping cuz chatgpt token limit")
            time.sleep(10)
    return response


def advancedMainContentExtraction(content, query, url):
    text = content
    a, sentences = sentenceSimilarity(query, text, url)

    if len(a) >= 10:
        a = a[0:10]
    #print(a)

    newArray = []
    for i in a:
        if i[0] not in newArray:
            if sentences.index(i[0]) - 1 >= 0:
                newArray.append(sentences[sentences.index(i[0]) - 1])
            newArray.append(i[0])
            if sentences.index(i[0]) + 1 < len(sentences):
                newArray.append(sentences[sentences.index(i[0]) + 1])

    #(newArray)
    return newArray


def websiteStatus(website):
    # can be either Right, Right-Center, Center, Left-Center, Left, Questionable, Conspiracy-Pseudoscience, Pro-Science, or Satire
    return websiteTrust[website]

def wikipediaEvidence(wikilink):
    url = wikilink
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')
    paragraphString = soup.findAll('p')

    firstparagraphs = 3
    paragraphParsed = []
    for i in paragraphString:
        if len(i) > 10:
            subPara = ''
            new = i.get_text()
            count = 0
            for j in new:
                if j != '[' and j != ']':
                    if count > 0 and new[count - 1] != '[':
                        if count < len(new) - 1 and new[count + 1] != ']':
                            subPara += j
                if count == 0:
                    subPara += j
                count += 1
            paragraphParsed.append(subPara)
        if firstparagraphs == 0:
            break
        firstparagraphs -= 1
    #print(paragraphParsed)
    return paragraphParsed

def checkIfWebsiteReliable(website):
    #print("START SEARCHING")
    query = cleanUrl(website)+" wikipedia"
    #print("Query: " + query)
    mainContent = ""
    wikipediaFound = False
    for i in search(query, tld="co.in", num=3, stop=3):
        #print(i)
        # print(cleanUrl(i))
        if cleanUrl(i) == "wikipedia.org":
            mainContent = wikipediaEvidence(i)
            wikipediaFound = True
            break
    # print(website)
    if wikipediaFound:
        chatGPTresponse = AskChatGPT("You are a professional fact checker. Given this website name: " + website + " and the information about it: " + str(mainContent) + " return to me a JSON object with 1 element: a boolean representing the reliability of the website. I am not asking you to search anything up, I am only asking you to make the best prediction based on the available evidence")
        return json.loads(isolateCurlyBrackets(chatGPTresponse)).get(next(iter(json.loads(isolateCurlyBrackets(chatGPTresponse)))))
    else:
        # print("Search Conclusion: No Wikipedia, Therefore False")
        return False

def AskGemini(prompt):
    response = model2.generate_content(prompt, safety_settings={HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE})
    print(response)
    return response.text

def isolateCurlyBrackets(input):
    finalString = ""
    start = False
    for i in input:
        if i == "{":
            start = True
        if i == "}":
            start = False
            finalString += i
        if start:
            finalString += i
    return finalString

def parseClaimContextResponse(GPT_Response):
    GPT_Response = GPT_Response.split("\"")
    substring = ""
    everythingList = []
    for i in GPT_Response:
        if any(c.isalpha() for c in i):
            if not any(c.isalpha() for c in substring):
                substring += i
            else:
                substring += "\"" + i + "\""
        elif any(c.isalpha() for c in substring):
            everythingList.append(substring)
            substring = ""
    count = 0
    claimList = []
    contextList = []
    for i in everythingList:
        if i.count(" ") > 3:
            if len(everythingList[count - 1]) < 10 and everythingList[count - 1].count(" ") <= 3 and "claim" in \
                    everythingList[count - 1].lower():
                claimList.append(i)
        if i.count(" ") > 3:
            if len(everythingList[count - 1]) < 10 and everythingList[count - 1].count(" ") <= 3 and "context" in \
                    everythingList[count - 1].lower():
                contextList.append(i)
        count += 1
    print(dict(zip(claimList, contextList)))
    return dict(zip(claimList, contextList))

initialPrompt = """You are a professional fact checker. Your job is to find multiple check worthy claims from this
article. The criteria are that these claims either contain the main points of the paragraph or it contains a concrete
 and specific claim that may have huge impacts if left unverified. Additionally, you have
 to return your answer to me in JSON format with the exact sentence. You
 have to provide context for the claim by compiling information from the sentences before that claim. It is imperative 
 that you keep the claim in it's original form, and you do not need to paraphrase the claim for clarity, since the context 
 will supply the fact checker with the information needed for clarity. Paraphrasing the claim instead of just leaving it in it's
 original form found will render this program useless, so please make sure you do not do that. Additionally, it is 
 equally as important and vital to have the claims as an entire sentence. From the beginning to where the period ends it. 
 Failure to do this will also result in the program not working. Make sure to keep the number of check-worthy
 claims short by only finding 1 around every 300 words. Here is the article: """
currentUrl = ""
@app.route('/receive_message', methods = ['POST'])
def receive_message():
    global currentUrl
    data = request.json
    GPT_Answer = {}
    currentUrl = data['data']
    print(data)
    print(currentUrl)

    mainContent = extractMainContent(currentUrl)
    if mainContent is not None:
        GPT_Answer = AskChatGPT(initialPrompt + mainContent)
        GPT_Answer = parseClaimContextResponse(GPT_Answer)

    return GPT_Answer

@app.route('/check_claim', methods = ['POST'])
def check_claim():
    data = request.json
    startTime = time.time()
    claim_question_list = data['data']
    claim = claim_question_list[0]
    context = claim_question_list[1]
    print(claim)

    queries = AskChatGPT(
        "You are a professional fact checker. Only return to me in a JSON object, the rephrase of this claim into a search refined query for google, but do not google it. Make sure you return no other keyvalues. And do not leave out any important details. Here's the claim: " + str(
            claim) + "And here is the context behind it to help you know more about what this claim is actually saying: " + context)

    # print(queries)
    queries = parseGPTJSON(str(queries), 3)
    # print("AFTER PARSE")
    # print(queries)
    # if type(queries) == "dict":
    #     if len(str(list(queries.keys()))) > len(str(list(queries.values()))):
    #         queries = list(queries.keys())
    #     else:
    #         queries = list(queries.values())

    # print(queries)

    evidenceContentList = []
    usedSites = []
    for j in queries:
        evidenceContentList.append(SearchOnGoogle(j, cleanUrl(currentUrl)))

    # print(evidenceContentList)
    sources = []
    filteredList = []
    sources = [i[0] for i in evidenceContentList[0]]
    finalEvidence = []
    for evidenceChunk in evidenceContentList:
        # print("START PRINTING I")
        for subContent in evidenceChunk:
            prompt = "Return to me a JSON object with a large string. I need you to extract the content from this text that answers the question of " + \
                     subContent[2] + " Here is the text: " + subContent[1]
            if countToken(prompt) > 15000:
                cosineSimilarityEvidence = advancedMainContentExtraction(subContent[1], subContent[2], subContent[0])
                while True:
                    evidenceTokenLength = countToken(str(cosineSimilarityEvidence))
                    if evidenceTokenLength > 15000:
                        cosineSimilarityEvidence = cosineSimilarityEvidence[
                                                   :len(cosineSimilarityEvidence) - evidenceTokenLength - 7500 * 4]
                    evidenceTokenLength = countToken(str(cosineSimilarityEvidence))
                    if evidenceTokenLength <= 15000:
                        break
                finalEvidence.append(cosineSimilarityEvidence)
                # accepts parameters of content, query, and url
            else:
                # print(prompt)
                GPTresponse = AskChatGPT(prompt)
                finalEvidence.append(GPTresponse)
            # print(subContent)
            # finalEvidence.append(advancedMainContentExtraction(subContent[1], subContent[2], subContent[0]))
        # print("DONE PRINTING I")

    # print(finalEvidence)

    prompt = "You are a professional fact checker. You are given a bunch of evidence compiled from many different sources: " + str(
        finalEvidence) + " You have just read all of the evidence. Now based on this return to me in a JSON object your rating of this claim being either False, Mostly False, Half True, Mostly True, and True here's the claim: " + claim + "Make sure to also return an explanation of your rating as well. Respond within 100 words. This is to make the fact checking explanation more user friendly. Also, make sure to state your rating of the claim in the first sentence. If there is not enough evidence to verify the claim, instead of rating the claim and providing an explanation, you return to me a question suitable for google search that will most likely yield the additional information needed to provide a full answer with enough evidence so that you can determine the rating of the claim. "
    # print(prompt)
    finalAnswer = AskChatGPT(prompt)
    if "True" not in str(json.loads(isolateCurlyBrackets(finalAnswer))[
                             next(iter(json.loads(isolateCurlyBrackets(finalAnswer))))]) and "False" not in str(
            json.loads(isolateCurlyBrackets(finalAnswer))[
                next(iter(json.loads(isolateCurlyBrackets(finalAnswer))))]) and "false" not in str(
            json.loads(isolateCurlyBrackets(finalAnswer))[
                next(iter(json.loads(isolateCurlyBrackets(finalAnswer))))]) and "true" not in str(
            json.loads(isolateCurlyBrackets(finalAnswer))[next(iter(json.loads(isolateCurlyBrackets(finalAnswer))))]):
        evidenceContentList = []
        for j in parseGPTJSON(finalAnswer, 3):
            evidenceContentList.append(SearchOnGoogle(j, cleanUrl(currentUrl)))
        sources.append([i[0] for i in evidenceContentList[0]])
        for evidenceChunk in evidenceContentList:
            # print("START PRINTING I")
            for subContent in evidenceChunk:
                prompt = "Return to me a JSON object with a large string. I need you to extract the content from this text that answers the question of " + \
                         subContent[2] + " Here is the text: " + subContent[1]
                if countToken(prompt) > 15000:
                    cosineSimilarityEvidence = advancedMainContentExtraction(subContent[1], subContent[2],
                                                                             subContent[0])
                    while True:
                        evidenceTokenLength = countToken(str(cosineSimilarityEvidence))
                        if evidenceTokenLength > 15000:
                            cosineSimilarityEvidence = cosineSimilarityEvidence[
                                                       :len(cosineSimilarityEvidence) - evidenceTokenLength - 7500 * 4]
                        evidenceTokenLength = countToken(str(cosineSimilarityEvidence))
                        if evidenceTokenLength <= 15000:
                            break
                    finalEvidence.append(cosineSimilarityEvidence)
                    # accepts parameters of content, query, and url
                else:
                    # print(prompt)
                    GPTresponse = AskChatGPT(prompt)
                    finalEvidence.append(GPTresponse)
        prompt = "You are a professional fact checker. You are given a bunch of evidence compiled from many different sources: " + str(
            finalEvidence) + " You have just read all of the evidence. Now based on this return to me in a JSON object your rating of this claim being either False, Mostly False, Half True, Mostly True, and True here's the claim: " + claim + "Make sure to also return an explanation of your rating as well. Make sure to talk as concisely as possible without leaving out important details. This is to make the fact checking explanation more user friendly. Also, make sure to state your rating of the claim in the first sentence. If there is not enough evidence to verify the claim, instead of rating the claim and providing an explanation, you return to me a question suitable for google search that will most likely yield the additional information needed to provide a full answer with enough evidence so that you can determine the rating of the claim. "
        # print(prompt)
        finalAnswer = AskChatGPT(prompt)

    factcheckdata = [claim, list(json.loads(finalAnswer).values())[0], list(json.loads(finalAnswer).values())[1], sources]
    return factcheckdata

if __name__ == '__main__':
    app.run(port=5000)
