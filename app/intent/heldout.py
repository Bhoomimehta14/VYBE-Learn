"""Held-out learner messages used ONLY to measure the intent head.

Never copy these into examples.py: they are the honest test of how the head
does on wording it has not seen. Written in a different voice from the
training rows (longer, chattier, different vocabulary).
"""

HELDOUT: dict[str, list[str]] = {
    "concept_question": [
        "could you break down what a z-score is",
        "I keep seeing the word variance, what does it actually mean",
        "what's the point of splitting data into train and test",
        "how come median is safer than mean when there are extremes",
        "is a null the same thing as a blank cell",
        "tell me what feature engineering involves",
        "what exactly is a confusion matrix",
        "why would a column have mixed types",
    ],
    "hint_request": [
        "could you drop me a tiny clue about this column",
        "any small nudge on which fix to try first?",
        "I'd like just a pointer, please don't solve it",
        "throw me a bone, what should I check",
        "can I have a little tip without the full answer",
        "give me a teeny hint on the next move",
        "a gentle push in the right direction would be great",
        "what's one thing I should notice here",
    ],
    "stuck_frustrated": [
        "ugh nothing here makes sense and i am about to quit",
        "I've reread this five times and I'm still totally lost",
        "honestly this is stressing me out, I can't follow any of it",
        "I feel like I'm the only one who doesn't understand this",
        "this whole thing is way over my head",
        "I'm ready to throw my laptop, why won't it click",
        "I'm completely blank, nothing is sticking",
        "everyone else seems fine and I'm just drowning here",
    ],
    "why_wrong": [
        "why did the agent say my pick was wrong",
        "I thought median was right, why was it marked incorrect",
        "can you explain why my answer didn't work",
        "what did I get wrong in that last step",
        "why isn't dropping the rows acceptable here",
        "my choice seemed fine, so where's the mistake",
        "how come the check failed on my fix",
        "what made my approach the wrong one",
    ],
    "next_step": [
        "ok I finished that, what do I do now",
        "what comes after cleaning this column",
        "I'm done with this part, where should I go next",
        "so what's the following stage in the course",
        "alright, that's sorted, what's up next for me",
        "can we move on to the modelling bit",
        "what should I tackle after this",
        "I think I'm ready for the next lesson",
    ],
    "example_request": [
        "show me one worked example with a few numbers",
        "can you walk through a tiny case so I can see it happen",
        "do you have a concrete sample I can look at",
        "illustrate that with a real-looking row of data",
        "I learn best from demos, can you run through one",
        "give me a quick scenario using actual values",
        "could you demonstrate that on a small table",
        "an example with sales figures would help me get it",
    ],
    "off_topic": [
        "who is the best cricket player ever",
        "what's a good recipe for pasta tonight",
        "tell me a joke about cats",
        "what's the weather like in Mumbai",
        "who won the world cup in 2018",
        "recommend a movie for the weekend",
        "how do I fix my bike chain",
        "what's the capital of Australia",
    ],
}
