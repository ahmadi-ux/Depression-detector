## Interfaces

These python files within the interfaces folder is where the magic happens. The different LLMs are called from these and are given the infomration that the user puts in such as llm, prompt, and file/text input.

## New Interfaces

To add a new LLM interface simply create a new .py file named that interface. If the new interface is using a Groq Api key then u simply need to utilize the groq_handler.py file in the common folder. This file reduces the amound of reduntant code in each interface that utilizes Groq. If the LLM is a stand alone Api key such as gemini then you must create the handler within either the Common folder if you plan to use multiple llms from the same api/website, or within the Interface as seen with the Gemini.py 