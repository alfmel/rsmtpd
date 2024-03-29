# RSMTPD: Research-oriented SMTP Daemon

RSMTPD is a modular and configurable SMTP server designed to improve the research of Spam, phishing and other
email-related topics.

## Status
RSMTPD is now at version 0.5.0 and supports the following features:
* Running as full, nearly RFC-5321 compliant server capable of delivering email through dovecot-lda
* Running as non-working email server with SMTP 521 response (RFC 7504) to any command presented
* Acting as a proxy to another full SMTP server, including TLS and SNI
* Logging commands and responses to transaction logs

Unsupported features:
* SFP/SenderID
* Signature verifications
* Any other form of Spam filtering


## ROAD MAP
* Version 0.6.0: Basic spam-reducing functionality (SPF, Sender ID, reputation tracking)
* ...
* Version 0.9.0: First beta release, internal API freeze
* Version 1.0.0: Available for general consumption

Notice there are no dates given for any release. I work on this project on my spare time, and I don't have a lot of it.
Feel free to contribute at any stage.

## Installation and Setup
I still don't have a good Python module setup for this, mostly because every example you look at and every site you read
(including the official Python docs) is either incomplete, obsolete or just wrong. So we'll do this the manual way for
now.

1. Clone the repository:
```commandline
git clone https://github.com/alfmel/rsmtpd.git
```

2. Enter the repo directory and set up the virtual environment:
```commandline
cd rsmtpd
python -m venv venv
source venv/bin/activate.sh
pip install -r requirements.txt
```

3. Modify the configuration files in `config` to meet your needs. (It is recommended to make a copy of the config
directory, like to `/etc/rsmptd` and modify the copy. You can specify the config file at start-up with the
`-c /path/to/config` argument.)

4. Run the server:
```commandline
./rsmtpd.py
```

### Configuration
Configuration starts with `config/rsmtpd.yaml`. This sets up the parameters for the listening server (daemon). Many of those options can also be specified in the command line.

Configuration then moves to `config/worker.yaml`. This controls the worker that is spawned on every incoming connection. (The file is read every time a new connection arrives, removing the need to restart the daemon every time you change configurations.) In the worker you specify the command handler configuration file (must be named `command_handler_{name}.yaml`). The command handler will contain the command handler chains for each SMTP command, along with some special ones such as `__OPEN__`, and `DEFAULT` for anything not explicitly defined.


## FAQ

### Why a new (and modular) SMTP Daemon?

I manage a small, personal domain. Spam is a big problem, and I can never tackle it effectively. A few years ago I wrote my thesis on `phishing email detection <http://scholarsarchive.byu.edu/etd/3103/>`_. I applied what I learned to my email server and it has worked very well. Now it's time to take my research (and spam filtering) to the next level. In order to do it, I need a fully modular SMTP server I can tinker with.

### Isn't the spam problem already solved?
No, it is not! Spammers continue to pound mail servers with all sorts of unsolicited junk. If you use Gmail or another large provider you don't notice the problem because they have their own effective but proprietary solutions. Other solutions like SpamAssassin and Spamhaus help, but are not appropriate for true academic research.

### How is RSMTPD different?
RSMTPD is entirely modular by design. For any given SMTP command, administrators can specify any number of command handlers (a handler chain) to determine how the server should respond to that command. The command handlers can also maintain shared state to pass information to other commands.

Let's take the RCPT command, for example. This is used in the SMTP transaction to indicate who will receive the email. With RSMTPD, we can create specific command handlers to check the email address is valid. And if the email address is not valid, we can also:

* Apply a delay in the response (tarpitting)
* Inform the delivery agent that this message is spam and should not be delivered
* Inform the reputation tracker that the client is a known spammer
* Reject the email after the DATA has been sent
* Feed the raw message to a content filter for training

And, when you think of something else you'd like to do or test, you simply add another command handler to the chain.

### Why write it in Python?
Python is one of the most commonly used programming languages in scientific research. It's simplicity (compared to C/C++ or Java) lowers the entry barrier for those wishing to use it. Python is also well-suited for writing network services. Yes, it may not have the performance of C/C++ or Java, but our emphasis is not on performance, but modularity. Even though RSMTPD will be fully capable of running in a production environment, performance and scalability will never be the driving factors behind its design.
