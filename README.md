# An AI and Gesture-Based Application to Assist People with Fine Motor Impairment in Creating Art

## A chrome extension combined with a python backend which automatically highlights check-worthy claims on websites you visit in order to provide online users with a more trustworthy experience

This was my sophomore year science research project. It utilizes chrome extension, the python flask framework for communication between python (backend) and chrome extension (frontend). It also incorporates the BERT model, ChatGPT's API, and Google search API to find sources, extract the relevant information, and verify the claim. Some functionality includes:

* Automation of entire fact checking process. The user only has to visit a news article and the fact checker will automatically run in the background. 
* User-friendly interface. Claims are highlighted with colors corresponding to their truthfulness (e.g. red for false, green for true etc...). Additionally, a short explanation and the sources used are provided in a little tooltip above the highlighted claim
* Trustworthy sources only. This program utilizes a database of well-known credible sources as well as known fake news websites compiled from <a href="https://mediabiasfactcheck.com/">Media Bias/Fact Check</a>. In the event that any website is not found on the database, Google search will return the wikipedia article of the website and ChatGPT will verify it based on the information provided by wikipedia. 

