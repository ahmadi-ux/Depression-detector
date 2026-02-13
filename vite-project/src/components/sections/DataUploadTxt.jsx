import { useState } from "react";
import ContactForm from "../ContactFormTxt";
import { Button } from "../ui/button";
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogTrigger,
} from "../ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup,
  DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu"

const buttonDetails = "rounded-xl shadow-md hover:scale-105 hover:bg-white transition-transform";
const dropdownMenuStyle = "focus:bg-gray-100 data-[highlighted]:bg-gray-100 cursor-pointer px-2 py-1";

const PROMPT_OPTIONS = [
  { value: "simple", label: "Simple (Binary Classification)" },
  { value: "structured", label: "Structured (Checklist)" },
  { value: "feature_extraction", label: "Feature Extraction (Metrics)" },
  { value: "chain_of_thought", label: "Chain-of-Thought (Reasoning)" },
  { value: "few_shot", label: "Few-Shot (Example Based)" },
  { value: "free_form", label: "Free-Form (Narrative)" },
];

/** Data Upload Section with dialog form for uploading Text
 * - Dialog with a contact form when button is clicked
*/
export default function DataUploadTxt() {
  const [open, setOpen] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState("Gemini");
  const [selectedPrompt, setSelectedPrompt] = useState("simple");

  return (
    <div className="h-auto flex flex-col items-center justify-center bg-yellow-100 p-4 px-8 py-16">
      <h2 className="text-5xl font-bold mb-4">Text Upload</h2>
      {/*<div className="w-full max-w-xl flex flex-col">*/}

      <p className="text-lg max-w-xl text-center">
      </p>
      <div className="flex justify-center mt-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="lg" className={buttonDetails}>Upload Text</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Text Upload</DialogTitle>
              <DialogDescription>
                Upload text to interface with the LLMs.
              </DialogDescription>
            </DialogHeader>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">Select Model Current Model = {selectedLLM}</Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="z-50 bg-white text-black shadow-xl border rounded-md p-1">
                   <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("Gemini")}>
                      Gemini
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("LLaMA")}>
                      LLaMA
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("ChatGPT")}>
                      Chat GPT
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("Kimi")}>
                      Kimi
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("Qwen")}>
                      Qwen Doesn't Work 
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("Compound")}>
                      Compound
                  </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            {/* Prompt Selection Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full">
                  Analysis Type: {PROMPT_OPTIONS.find(p => p.value === selectedPrompt)?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="z-50 bg-white text-black shadow-xl border rounded-md p-1 w-full max-h-64 overflow-y-auto">
                {PROMPT_OPTIONS.map((option) => (
                  <DropdownMenuItem 
                    key={option.value}
                    className={dropdownMenuStyle} 
                    onClick={() => setSelectedPrompt(option.value)}
                  >
                    {option.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Help Text */}
            <div className="text-xs text-gray-600 mt-2 p-2 bg-gray-50 rounded">
              <p className="font-semibold mb-1">Analysis Types:</p>
              <ul className="space-y-1">
                <li><strong>Simple:</strong> Quick binary classification with confidence scores</li>
                <li><strong>Structured:</strong> Detailed checklist of depression markers</li>
                <li><strong>Feature Extraction:</strong> Linguistic metrics and statistics</li>
                <li><strong>Chain-of-Thought:</strong> Step-by-step reasoning process</li>
                <li><strong>Few-Shot:</strong> Example-based assessment</li>
                <li><strong>Free-Form:</strong> Clinical narrative analysis</li>
              </ul>
            </div>
            
            <ContactForm onSuccess={() => setOpen(false)} llm={selectedLLM} prompt={selectedPrompt} />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}