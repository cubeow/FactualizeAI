previousResponse = "";
previousTab = "";
chrome.runtime.onInstalled.addListener(() => {
    console.log("hi");
});
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url != previousTab && changeInfo.url != undefined)
  {
    sendMessageToPython(changeInfo.url);
    console.log(changeInfo.url);
    previousTab = changeInfo.url;
  }
});
function sendMessageToPython(message) {

  if (previousResponse != message) {
    previousResponse = message;

    fetch('http://localhost:5000/receive_message', {
      method: 'POST',
      body: JSON.stringify({ data: message }),
      headers: {
        'Content-Type': 'application/json'
      },
    })
    .then(response => response.json()) 
    .then(data => {
      
      console.log("Response from server:", data);
      claims = [];
      questions = [];
      Object.entries(data).forEach(([key, value]) => { 
        console.log('Key:', key);
        console.log('Value:', value);
        fetch('http://localhost:5000/check_claim', {
          method: 'POST',
          body: JSON.stringify({ data: [key, value] }), 
          headers: {
            'Content-Type': 'application/json'
          },
        })
        .then(response => response.json())
        .then(data => { 
          console.log(data);
          chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
            if (tabs && tabs.length > 0) {
             
              chrome.tabs.sendMessage(tabs[0].id, { message: "execute_function", param1: data[0], param2: data[1], param3: data[2], param4: data[3] });
            } else {
              console.error("No active tabs found.");
            }
          });
          });
        });

     });

      
    }
  }