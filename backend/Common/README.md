## Common

This Common folder holds code/files that are utilized in multiple places throughout the project allowing for more readanle code so that new users or contributers can quickly understand what they must actually add to get the desired outcome.  

## prompts.py

This file is where the different prompt options are held and called throughout the project to interact with the LLMs this makes for easy editing and less total lines as they are all in one place only. 

## engineUtils.py 

This file is where most of the work is done on both the uploaded data and the output pdfs.  We first extract the text from the uploaded data and format it into a universal format.  We than parse over the LLM output to format it into a pdf output based on the type of prompt chosen and the number of files uploaded. That is where most of the meat is from since each prompt provides different parameters to look for, so each prompt needs to have different formatting of their ouputs.

## groq_handler.py

This file is where the Groq interfaces are doing their work such as extracting data from files after engineUtils formats it such as different rows, columns, and also mapping different parts to each other and also formatting the API output so that its consistent. It also analyzes the token amount because as we are developing this we are using a free api key. The largest section of this file is to parse over csv files as they need more formatting.