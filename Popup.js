document.addEventListener("DOMContentLoaded", function(){ //Waits until the content of the website is loaded

    document.getElementById("button1").addEventListener("click",function(){ // if the popup button gets clicked
        alert("The button has been clicked on"); // you can use alert to print stuff, but its really annoying
        var body = document.getElementsByTagName("body")[0].style.backgroundColor = "aqua";
    });
});