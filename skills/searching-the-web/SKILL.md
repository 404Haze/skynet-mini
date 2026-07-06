---
name: searching-the-web
description: >
  Use when the user asks for current information, facts, or anything
  that requires looking up data on the internet. Triggers on questions
  like "search for", "look up", "find information about", "what is the
  latest", "who is", "news about".
---

# Searching the Web

Use the `web_search` tool to find current information from DuckDuckGo.

## When to use this skill

- User asks about current events, news, or recent information
- User wants facts, definitions, or explanations you're unsure about
- User asks about latest versions, releases, or updates
- User wants to compare options, prices, or recommendations
- User asks for documentation or reference material

## How to search effectively

1. Formulate a clear, specific search query
2. Call `web_search(query="your query")` — max_results defaults to 5
3. Review results and extract the most relevant information
4. Present findings with source URLs

## What NOT to do

- Don't search for things you're already confident about
- Don't run more than 3 searches for a single user request
- Don't present raw search results — summarize and contextualize
- Don't make up information if search returns nothing useful
