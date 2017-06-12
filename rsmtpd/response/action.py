# Command execution normal (even if it results in error condition)
OK = "OK"

# Valid response to DATA command, telling command processor to issue 354 and wait for <CRLF>.<CRLF>
CONTINUE = "continue"

# Error condition leaving us in an invalid or incorrect state
INVALID = "invalid"

# Close the connection after sending the given response
CLOSE = "close"

# Close connection immediately, without a response
FORCE_CLOSE = "force_close"
