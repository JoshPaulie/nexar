# How LLMs almost nuked Nexar

Frankly, we lost the plot there for a bit.

The goal of this project was simple:

    - async
    - robust models
    - basic cache
    - precise rate limiter
    - simple client
    - more SDK than wrapper, but not a full fledged framework

But the Devil (LLMs) whispered in my ear... "Why not make this ""production ready""? Why not add robust redis rate limiting, suitable for distributed applications? Why not add a distributed cache? Why not add more features? Why not make it perfect?"

And so I did. Redis, "LLM agent frameworks" like Get Shit Done, long running feature and review agents.

What did I get? I got a bloated, out-of-scope mess. I abandoned the project, having lost my sense of ownership. This was no longer something I was proud of and wanted to share.

But I was proud of the roots, what I had designed before. It was my perfect library, exactly what I needed. So I stripped out all the superfluous nonsense and returned to the core principles.

For that reason, the entire git history has been squashed in preparation of a new v1.0.0 release.
