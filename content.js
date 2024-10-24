console.log("hi")

function splitIntoSentences(text) {
  const prefixes = "(Mr|St|Mrs|Ms|Dr)[.]";
  const suffixes = "(Inc|Ltd|Jr|Sr|Co)";
  const starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\\s|She\\s|It\\s|They\\s|Their\\s|Our\\s|We\\s|But\\s|However\\s|That\\s|This\\s|Wherever)";
  const acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)";
  const websites = "[.](com|net|org|io|gov|edu|me)";

  const exclusionRegex = new RegExp(`${prefixes}|${suffixes}|${starters}|${acronyms}|${websites}`, 'g');

  const sentences = text.split(/(?<=[.!?])\s+/);

  return sentences
}

function editDistance(s1, s2) {
  s1 = s1.toLowerCase();
  s2 = s2.toLowerCase();

  var costs = new Array();
  for (var i = 0; i <= s1.length; i++) {
    var lastValue = i;
    for (var j = 0; j <= s2.length; j++) {
      if (i == 0)
        costs[j] = j;
      else {
        if (j > 0) {
          var newValue = costs[j - 1];
          if (s1.charAt(i - 1) != s2.charAt(j - 1))
            newValue = Math.min(Math.min(newValue, lastValue),
              costs[j]) + 1;
          costs[j - 1] = lastValue;
          lastValue = newValue;
        }
      }
    }
    if (i > 0)
      costs[s2.length] = lastValue;
  }
  return costs[s2.length];
}

function similarity(s1, s2) {
  var longer = s1;
  var shorter = s2;
  if (s1.length < s2.length) {
    longer = s2;
    shorter = s1;
  }
  var longerLength = longer.length;
  if (longerLength == 0) {
    return 1.0;
  }
  return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
}

function isElementVisible(element) {
  const style = window.getComputedStyle(element);
  return style.display !== 'none' && style.visibility !== 'hidden';
}

function getFirstAndLastWords(inputString) {
	inputString = inputString.replace(/"/g, "").replace(/'/g, "").replace(/\(|\)/g, "");
  if (inputString.slice(-1) == "."){
      inputString = inputString.substring(0, inputString.length-1);
  }

  var newString = ""
  for (let i = 0; i < inputString.length; i++) {
    if (inputString[i] !== String.fromCharCode(160)){
    	newString += inputString[i]
    }
    else {
    	newString += " "
    }
	}
  
  var splitArray = newString.split(" ");
  var newArray = [] 
  splitArray.forEach(function (item){
    if (/[^ \t\n\r\v\f]/.test(item)) {
      newArray.push(item)
    }
  })
  const firstWord = newArray[0];
  const lastWord = newArray[newArray.length - 1];
  return { firstWord, lastWord };
}

function modifyFirstWord(paragraphInnerHTML, firstWord) {
  var paragraphMapStarter = paragraphInnerHTML.replace("&lt;", "<");
      paragraphMapStarter = paragraphInnerHTML.replace("&gt;", ">");
      var paragraphMap = []
      var paragraphMapString = ""
      var startWriting = false
      for (var j=0; j < paragraphMapStarter.length; j++){
        if (paragraphMapStarter[j] == "<"){
          startWriting = false
          if (paragraphMapString !== ""){
              paragraphMap.push(paragraphMapString)
            }
          paragraphMapString = ""
        }
        if (startWriting) {
          paragraphMapString += paragraphMapStarter[j]
        }
        if (paragraphMapStarter[j] == ">"){
          if (startWriting) {
            startWriting = false
            if (paragraphMapString !== ""){
              paragraphMap.push(paragraphMapString)
            }
            paragraphMapString = ""
          } else{
            startWriting = true
          }
        } 
        
      }
      
      paragraphMap = paragraphMap.toString()
      // console.log("PARAGRAPH MAP")
      // console.log(paragraphMap);
      var newFirstWord = ""
            // if the first word is inside the nested element but not the last word
      if (paragraphMap.includes(firstWord) && !paragraphMap.includes(lastWord)){
        for (var k = 0; k < paragraphInnerHTML.length; k++){
          newFirstWord += paragraphInnerHTML[k]
          if (newFirstWord.includes(firstWord)){
            break;
          }
        }
      }
      

      if (newFirstWord !== ""){
        firstWord = newFirstWord;
      }

      return firstWord
}

let param1 = ""
let previousParam1 = "a" 

function modifyToolTipText(toolTipText){
	var toolTipString = ""
  var toolTipLink = ""
  var newToolTipList = []
  var addLink = false
	for (var i = 0; i < toolTipText.length; i++){
  	if (!addLink){
      if (toolTipText[i] !== ","){
        toolTipString += toolTipText[i]
      } else if (i < toolTipText.length - 7 && toolTipText.substring(i+1, i+5) === "http"){
          addLink = true
        }
     }else{
     		
        if (toolTipText[i] === ","){
        	newToolTipList.push("<a href=" + toolTipLink + ">" + toolTipString + "</a>")
          toolTipLink = ""
          toolTipString = ""
          addLink = false
        }else{
        	toolTipLink += toolTipText[i]
        }
     }
	}
  var ToolTipString = ""
  for (i = 0; i<newToolTipList.length; i++){
  	ToolTipString += newToolTipList[i] + " "
  }
  return ToolTipString
}

function filterString(inputString) {
    var regex = /[^\x20-\x7E"']/g;
    var filteredString = inputString.replace(regex, '');
    return filteredString;
}

function editFirstLastWord(firstWord, lastWord, paragraph){
		  console.log("firstWord: " + firstWord);
          console.log("lastWord: " + lastWord);
          console.log(paragraph.includes(lastWord))
          linkString = paragraph.substring(paragraph.lastIndexOf(lastWord)+lastWord.length,paragraph.lastIndexOf(lastWord)+lastWord.length+4);
          console.log(linkString)
          if (linkString.includes("</a>")){
          	lastWord=linkString
          }
          console.log("lastWord: " + lastWord);
          return firstWord, lastWord;
}

function highlightSentence(sentence, highlightColor, toolTipText, sources){
  console.log(sources)
  let claimRating = highlightColor;
  let className = "tooltip" + highlightColor.toLowerCase();
  className = className.replace(/\s/g, '');
  switch(highlightColor.toUpperCase()){
    case "TRUE":
      highlightColor = "rgb(60, 183, 30)"
      break;
    case "MOSTLY TRUE":
      highlightColor = "rgb(51, 255, 0)"
      break;
    case "HALF TRUE":
      highlightColor = "rgb(200, 255, 0)"
      break;
    case "MOSTLY FALSE":
      highlightColor = "rgb(255, 149, 0)"
      break;
    case "FALSE":
      highlightColor = "rgb(255, 0, 0, 0.655)"
      break;
  }

  var paragraphs = document.getElementsByTagName("p");
  for (var i=0, max=paragraphs.length; i < max; i++){
    if (isElementVisible(paragraphs[i])){
      var sentenceArray = splitIntoSentences(paragraphs[i].textContent);
      // checking if there is a nested element

      sentenceArray.forEach(function (item, index) {
          item = item.trim();
          console.log(item);
          console.log(similarity(item, sentence));
        if (similarity(item, sentence) >= 0.5){
          console.log(sentence);
          var newFirstWord = modifyFirstWord(paragraphs[i].innerHTML, firstWord);
          if (newFirstWord !== ""){
            firstWord = newFirstWord;
          }

		  console.log(sentence);
          var { firstWord, lastWord } = getFirstAndLastWords(item);
          firstWord = filterString(firstWord);
          lastWord = filterString(lastWord);
          var sourceText = '';
          // Adding sources to the tooltip text
          if (sources && sources.length > 0) {
            sourceText = sources.map((source, index) => `[${index + 1}]`).join('');
            toolTipText += '<br>Sources: ' + sources.map((source, index) => `<a href="${source}" target="_blank" style="color: blue">${index + 1}</a>`).join(', ');
        }
          firstWord, lastWord = editFirstLastWord(firstWord, lastWord, paragraphs[i].innerHTML);
          paragraphs[i].innerHTML = paragraphs[i].innerHTML.replace(firstWord, `<div class="tooltip" id="normal_tooltip" style="display: inline; font-size: inherit;"><mark style="background-color: ${highlightColor}!important">` + firstWord);
          paragraphs[i].innerHTML = paragraphs[i].innerHTML.replace(lastWord, lastWord + `</mark><div class="${className}"><h3>${claimRating}</h3>${toolTipText}</div></div>`)
        } else if (similarity(item.split(":")[0], sentence) >= 0.5){
          // console.log("COLON" + item);
          var { firstWord, lastWord } = getFirstAndLastWords(item);
          firstWord = filterString(firstWord);
          lastWord = filterString(lastWord);
          var sourceText = '';
          if (sources && sources.length > 0) {
            sourceText = sources.map((source, index) => `[${index + 1}]`).join('');
            toolTipText += '<br>Sources: ' + sources.map((source, index) => `<a href="${source}" target="_blank" style="color: blue">${index + 1}</a>`).join(', ');
        }
        	firstWord, lastWord = editFirstLastWord(firstWord, lastWord, paragraphs[i].innerHTML);
          
          paragraphs[i].innerHTML = paragraphs[i].innerHTML.replace(firstWord, `<div class="tooltip" id="normal_tooltip" style="display: inline; font-size: inherit;"><mark style="background-color: ${highlightColor}!important">` + firstWord);
          paragraphs[i].innerHTML = paragraphs[i].innerHTML.replace(lastWord, lastWord + `</mark><div class="${className}"><h3>${claimRating}</h3>${toolTipText}</div></div>`)
        }
      });
    }
  }
}

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if(request.message === "execute_function") {
        param1 = request.param1;
        var param2 = request.param2;
        var param3 = request.param3;
        var param4 = request.param4;
        // console.log("made it here")
        if (param1 !== previousParam1){
          previousParam1 = param1;
          console.log("Sentence: " + param1);
          console.log("highlightColor: " + param2);
          console.log("explanation: " + param3)
          // console.log("toolTipText" + param3);

          // param3 = modifyToolTipText(param3)
          highlightSentence(param1, param2, param3, param4);
        }
      }
    }
  );