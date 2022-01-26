# Proof of Concept only

from requests import post

post(
    "https://hooks.slack.com/services/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",
    json={"text": "Hello World from your Bot!"},
)
