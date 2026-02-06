# Depression-detector

## Research Goal 
Can LLMs predict self-reported depression and what specific language patterns can be used to identify depression among students in educational contexts?

## The Challenge
Depression among college students has reached crisis levels, with recent studies showing:
  * 44% of college students report symptoms of depression
  * Traditional screening relies on self-report surveys (PHQ-9, BDI-II) administered infrequently
  * Students often don't seek help until symptoms are severe
  * Existing methods don't capture temporal changes or provide early warning signals

## Methodology
Phase 1: Model Development
  * Public datasets fed into Llama 3.1 with (8B paramerters)
  * Zero-shot GPT-4 usage via API after Llama's integration
  * Zero-shot Gemini 1.5 via Api after GPT and Llama
  * Compare Performances via Accuracy and F1
