# 🚗 Toy Car HTTP Security Lab

A hands-on cybersecurity laboratory for learning how to identify and prevent security vulnerabilities in HTTP-based communication.

The project simulates a **toy car controlled over HTTP** and provides attack scenarios, interception tools, a server, and student exercises to demonstrate concepts such as **authentication, integrity, replay protection, and secure request generation**.

---

## 📌 Project Overview

The Toy Car HTTP Security Lab provides a controlled environment where students can study how an HTTP-based IoT-style system works and how an attacker can manipulate its communication.

The basic communication model is:

```text
┌──────────────┐
│     User     │
│   / Client   │
└──────┬───────┘
       │
       │ HTTP Request
       ▼
┌──────────────┐
│    Server    │
└──────┬───────┘
       │
       │ Command
       ▼
┌──────────────┐
│   Toy Car    │
│  Simulation  │
└──────────────┘
```

The lab introduces security weaknesses by allowing HTTP traffic to be inspected and manipulated.

Students then implement or test security mechanisms to understand how these attacks can be prevented.

---

## 🎯 Objectives

The main objectives of this project are to:

* Understand HTTP-based client-server communication.
* Understand how an IoT device can be controlled remotely.
* Observe insecure HTTP communication.
* Understand request interception and manipulation.
* Study common attack scenarios.
* Implement secure request-generation techniques.
* Verify the authenticity and integrity of requests.
* Understand replay protection.
* Learn the importance of server-side validation.
* Practice cybersecurity concepts in a controlled environment.

---

## 🔐 Security Concepts

The project focuses on several important security concepts.

### Authentication

Authentication ensures that the server can determine whether a request comes from a legitimate user.

```text
Client
   │
   │ Credentials / Authentication
   ▼
Server
   │
   ├── Valid → Accept
   │
   └── Invalid → Reject
```

### Integrity

Integrity ensures that a request has not been modified while being transmitted.

For example:

```text
Original Request:
MOVE = FORWARD

Attacker modifies:

MOVE = BACKWARD
```

A properly protected request should allow the server to detect this modification.

### Replay Protection

An attacker may capture a valid request and send it again later.

```text
Client ──────► Server
       Valid Request

       ↓ Intercepted

Attacker ────► Server
       Replayed Request
```

The server should be able to recognize that the request is old or has already been used.

### Authorization

Authentication answers:

> "Who are you?"

Authorization answers:

> "Are you allowed to perform this action?"

Both are important for a secure system.

### Secure Request Generation

The project includes functionality for generating and validating protected requests so that commands cannot simply be modified or replayed.

---

# 📂 Project Files

| File                  | Purpose                                                                            |
| --------------------- | ---------------------------------------------------------------------------------- |
| `README.md`           | Project documentation and instructions                                             |
| `HOWTO.html`          | HTML-based instructions for using the laboratory                                   |
| `how_to.pdf`          | PDF version of the laboratory instructions                                         |
| `server.py`           | Implements the HTTP server and processes client requests                           |
| `carsim.py`           | Simulates the toy car and its movement/commands                                    |
| `protocol.py`         | Defines the communication/security protocol used by the project                    |
| `wire.py`             | Handles the representation/transport of messages between components                |
| `interceptor.py`      | Simulates interception of communication between client and server                  |
| `attack_tests.py`     | Contains tests demonstrating attack scenarios and security weaknesses              |
| `scenarios.py`        | Defines different laboratory scenarios and test situations                         |
| `labusers.py`         | Provides user/account information used by the lab                                  |
| `student_solution.py` | File intended for students to implement or complete security-related functionality |
| `ui.py`               | Provides the user interface for interacting with the laboratory                    |

---

# 🏗️ System Architecture

The main components interact approximately as follows:

```text
                    ┌───────────────────┐
                    │       ui.py       │
                    │    User Interface │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Client/User     │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │    protocol.py   │
                    │ Communication /  │
                    │ Security Protocol │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │      wire.py      │
                    │ Message Transport │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  interceptor.py   │
                    │ Attack / Traffic  │
                    │    Interception   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     server.py     │
                    │   HTTP Server     │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     carsim.py     │
                    │   Toy Car Model   │
                    └───────────────────┘
```

Supporting components:

```text
labusers.py
     │
     └── User/account information

scenarios.py
     │
     └── Laboratory scenarios

attack_tests.py
     │
     └── Security/attack testing

student_solution.py
     │
     └── Student implementation

HOWTO.html / how_to.pdf
     │
     └── Laboratory instructions
```

---

# ⚙️ How the Lab Works

The laboratory follows a simple request-and-response model.

### 1. User sends a command

The user selects an action for the toy car.

Examples:

```text
FORWARD
BACKWARD
LEFT
RIGHT
STOP
```

### 2. Request is created

The client creates an HTTP request containing the command and relevant protocol information.

```text
User Command
     │
     ▼
HTTP Request
     │
     ▼
Protocol Processing
```

### 3. Request travels through the communication layer

The request passes through the project's communication components.

The `interceptor.py` component can be used to demonstrate what can happen when an attacker is able to observe or manipulate traffic.

### 4. Server receives the request

`server.py` receives and processes the request.

The server should verify the security properties of the request before executing the command.

### 5. Toy car executes the command

If the request is valid:

```text
Valid Request
     │
     ▼
Server
     │
     ▼
Toy Car
     │
     ▼
Command Executed
```

If the request fails security checks:

```text
Invalid Request
     │
     ▼
Server
     │
     ▼
Request Rejected
```

---

# 🧪 Attack Testing

`attack_tests.py` provides attack/security testing functionality.

The laboratory can be used to demonstrate scenarios such as:

### Request Modification

```text
Original:

COMMAND = FORWARD

       ↓

Attacker modifies request

       ↓

COMMAND = BACKWARD
```

A secure implementation should detect the modification.

### Replay Attack

```text
Valid Request
     │
     ▼
Captured by attacker
     │
     ▼
Sent again later
     │
     ▼
Server detects replay
     │
     ▼
Rejected ❌
```

### Unauthorized Request

A request from an unknown or unauthorized user should not be accepted.

---

# 🧑‍💻 Student Exercise

The `student_solution.py` file is intended for student implementation.

Students can use the provided project components and laboratory scenarios to understand the protocol and implement the required security functionality.

The general workflow is:

```text
Understand Protocol
       ↓
Study Existing Implementation
       ↓
Run Laboratory
       ↓
Observe Attack
       ↓
Implement Security Mechanism
       ↓
Run Attack Tests
       ↓
Verify Protection
```

---

# 🚀 Getting Started

## Requirements

Make sure Python is installed on your system.

Check the Python version:

```bash
python --version
```

or:

```bash
python3 --version
```

No external hardware is required because the project contains a software-based toy car simulation.

---

## Clone the Repository

```bash
git clone https://github.com/mohammedarshkhan5-create/toy-car-http-security-lab.git
```

Enter the project directory:

```bash
cd toy-car-http-security-lab
```

---

## Run the Laboratory

The exact execution flow depends on the laboratory scenario.

Start by reading:

```text
HOWTO.html
```

or:

```text
how_to.pdf
```

These files provide the detailed instructions for running the laboratory.

The main Python components include:

```text
server.py
ui.py
attack_tests.py
student_solution.py
```

Use the instructions provided with the lab before running individual components.

---

# 🔍 Recommended Learning Order

If you are new to the project, the following order is recommended:

### Step 1 — Read the documentation

Start with:

```text
README.md
    ↓
HOWTO.html / how_to.pdf
```

### Step 2 — Understand the protocol

Read:

```text
protocol.py
wire.py
```

### Step 3 — Understand the toy car

Read:

```text
carsim.py
```

### Step 4 — Understand the server

Read:

```text
server.py
```

### Step 5 — Study the users and scenarios

Read:

```text
labusers.py
scenarios.py
```

### Step 6 — Study the attack mechanism

Read:

```text
interceptor.py
attack_tests.py
```

### Step 7 — Complete the student implementation

Work with:

```text
student_solution.py
```

### Step 8 — Run the tests

Use:

```text
attack_tests.py
```

to verify the behavior of the implementation.

---

# 🧩 Component Summary

## `server.py`

The server-side component of the laboratory.

It receives client requests, processes them, performs the necessary checks, and controls the simulated toy car.

---

## `carsim.py`

Provides the toy car simulation.

It represents the device that ultimately receives commands such as movement instructions.

---

## `protocol.py`

Contains the project's communication protocol.

This is one of the most important files for understanding how requests are constructed, processed, and secured.

---

## `wire.py`

Provides the communication/message transport layer used between components.

It helps simulate how messages travel through the system.

---

## `interceptor.py`

Represents an attacker positioned between communicating components.

It can be used to demonstrate the security consequences of allowing an attacker to observe or manipulate communication.

Conceptually:

```text
Client
  │
  ▼
Interceptor
  │
  ▼
Server
```

---

## `attack_tests.py`

Contains security/attack tests.

It can be used to determine whether the implementation correctly handles malicious or invalid requests.

---

## `scenarios.py`

Contains predefined laboratory scenarios.

These scenarios make it easier to reproduce different security situations.

---

## `labusers.py`

Contains the users or credentials required by the laboratory environment.

---

## `student_solution.py`

The main file intended for student-side security implementation or experimentation.

---

## `ui.py`

Provides the user interface through which the laboratory can be interacted with.

---

# 🛡️ Security Model

The overall security goal can be represented as:

```text
             HTTP Request
                  │
                  ▼
        ┌──────────────────┐
        │ Authentication   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Integrity Check  │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Replay/Freshness │
        │      Check       │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  Authorization   │
        └────────┬─────────┘
                 │
                 ▼
          Execute Command
```

A request should only reach the toy car when the required security checks succeed.

---

# 📊 Expected Learning Outcomes

After completing this laboratory, students should be able to:

* Explain how HTTP communication works.
* Explain client-server architecture.
* Identify security weaknesses in HTTP-based IoT systems.
* Understand request interception.
* Explain authentication and authorization.
* Explain data integrity.
* Explain replay attacks.
* Understand secure request generation.
* Test security mechanisms against attacks.
* Analyze why server-side validation is important.
* Apply cybersecurity principles to an IoT-style system.

---

# 🔮 Possible Future Enhancements

The project can be extended with:

* HTTPS/TLS communication
* Digital signatures
* Stronger authentication
* Role-based access control
* Improved replay protection
* Secure key management
* Security event logging
* Automated attack detection
* Web-based security dashboard
* Physical IoT/toy-car hardware integration
* Additional attack scenarios

---

# ⚠️ Disclaimer

This project is intended for **educational and authorized cybersecurity testing only**.

Do not use the interception or attack functionality against systems, devices, networks, or services without explicit authorization.

---

# 📄 Documentation

Additional laboratory instructions are available in:

* `HOWTO.html`
* `how_to.pdf`

These should be consulted for detailed setup and laboratory procedures.

---

## 👨‍💻 Project

**Toy Car HTTP Security Lab**

A practical cybersecurity laboratory for understanding and testing the security of HTTP-based IoT-style communication.
