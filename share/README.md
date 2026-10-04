# Toy-Car HTTP Interceptor Assignment

This take home project is about the messages between a (client) web page and a car controlling server, with an
attacker sitting in between.  Scenarios 0 to 5 show different scenarios that can occur when an attacker is able to see your network traffic and alter it.  In scenario 6 inside the `student_solution.py`, you are expected to come up with defence techniques that will stop the demonstrated attack scenarios yourself.

The assingment code requires Python 3 only.  You do not need to install anything extra.

You can watch the demo video that will be shared with you to understand each scenario in the project.

## Start

```bash
cd /path/to/this/folder
python3 server.py
```

Open <http://localhost:8000> in your browser.

## The page

| Panel | What it does |
|---|---|
| **Client** | arrow buttons that send commands to the car |
| **Interceptor** | the attacker.  Hold a request, change it, drop it, delay it, send it again |
| **Car server** | checks each request, then moves the car or refuses |

Hovering the mouse over an element explains it's purpose.

## Scenarios

Choose one at the top of the page.  **Reset Scenario** puts everything back
to the start.

| # | Scenario | What is new |
|---|---|---|
| 0 | Client and car | no attacker yet |
| 1 | Plain HTTP | the Interceptor appears |
| 2 | Hash | each request carries a fingerprint of its body |
| 3 | Encryption | the body is scrambled |
| 4 | Authentication / Access Control | one account, a password, and rules for what it may do |
| 5 | Maintenance access | a second door on the car, opened with a five-digit code |
| 6 | Student Solution | your code |

Scenarios 0 to 5 are covered in the recorded lecture.  Scenario 6 runs
`student_solution.py`.

## Your job

Edit **`student_solution.py`** and nothing else.

**[HOWTO.html](HOWTO.html)** walks through the file: where each kind of
change goes, with the real code, and how to test it.  Open it in your browser (or use the PDF) and read it next (it prints well if you want it on paper).

To get started:

1. Switch to **Student Solution**.
2. Change one thing in `student_solution.py`.  Save.  Press **Reset Scenario**.
3. Press a button and read the logs.
4. Press **Run security checks**.  Each line is one attack.  **FAIL** means
   that attack still works.

Aim for all nine.  There is no single right design.

## What the attacker can do

- read every request
- change any part of it
- make up new requests
- drop or delay a request
- send an old request again
- see how long the car took to answer

The Interceptor sees only what goes over the network.  It never reads your
file.  You can read every secret in the source code; the attacker cannot.

## The account

One account, `student`, you are expected to find the password via techniques previously taught, this password will have to be used from scenario 4 onwards. Type the password in the Client panel.


## Folder

```
student_solution.py   EDIT THIS ONE
HOWTO.html            how to edit it (open in a browser)
how_to.pdf            same how to file in PDF  do not edit
README.md             this file
server.py             the web server           do not edit
ui.py                 the web page             do not edit
protocol.py           scenarios 0-5            do not edit
scenarios.py          the scenario list        do not edit
interceptor.py        the attacker             do not edit
carsim.py             the car                  do not edit
wire.py               request <-> text         do not edit
labusers.py           the account and password  do not edit
attack_tests.py       the nine checks          do not edit, just run it
```

The car, the page and the checks keep working around whatever you write in
`student_solution.py`.  If you break one of the other files, download the
project again.

## Submission

Students can prepare a report on the solutions that they come up with for defence against the attacks presented in this scenario. 

## Notes

Everything in this project is a weak security implmentation on purpose. Do not copy any of it into real software.
We acknowledge the use of LLMs in editing and formatting of this code base.
