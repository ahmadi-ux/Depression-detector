import { useState } from "react";
import ContactForm from "../ContactForm";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu"

const buttonDetails = "rounded-xl shadow-md hover:scale-105 hover:bg-white transition-transform";
const dropdownMenuStyle = "focus:bg-gray-100 data-[highlighted]:bg-gray-100 cursor-pointer px-2 py-1";

/** Data Upload Section with dialog form for uploading files
 * - Dialog with a contact form when button is clicked
*/
export default function DataUpload() {
  const [open, setOpen] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState("Gemini");

  return (
    <div className="h-auto flex flex-col items-center justify-center bg-blue-100 p-4 px-8 py-16">
      <h2 className="text-5xl font-bold mb-4">Data Upload</h2>
      {/*<div className="w-full max-w-xl flex flex-col">*/}

      <p className="text-lg max-w-xl text-center">
      </p>
      <div className="flex justify-center mt-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="lg" className={buttonDetails}>Upload Files</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>File Upload</DialogTitle>
              <DialogDescription>
                Upload a PDF or document to interface with the LLMs.
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
                      Qwen
                  </DropdownMenuItem>
                  <DropdownMenuItem className={dropdownMenuStyle} onClick={() => setSelectedLLM("Compound")}>
                      Compound
                  </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <ContactForm onSuccess={() => setOpen(false)} llm={selectedLLM} />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}