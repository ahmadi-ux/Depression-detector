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
import gitIcon from "../../assets/github-mark.png";
import linkedInIcon from "../../assets/InBug-Black.png";

const linkButtons = `flex justify-between mb-4 gap-4`;
const buttonDetails = "rounded-xl shadow-md hover:scale-105 hover:bg-white transition-transform";

/** Contact Me Section with dialog form for sending messages to me
 * - Displays contact links (GitHub, LinkedIn)
 * - Dialog with a contact form when button is clicked
*/
export default function Contactme() {
  const [open, setOpen] = useState(false);

  return (
    <div className="h-auto flex flex-col items-center justify-center bg-orange-100 p-4 px-8 py-16">
      <h2 className="text-5xl font-bold mb-4">Contact Me</h2>
      <h2 className="text-3xl font-bold mb-4">Links</h2>
      {/*<div className="w-full max-w-xl flex flex-col">*/}
      <div className="w-full max-w-xs flex flex-col">
        <div className="w-full max-w-xl flex flex-col">
          <div className="flex justify-between">
            <div className={linkButtons}>
              <Button asChild variant="outline" className={buttonDetails}>
                <a href="https://github.com/Justin-Ott" target="_blank" rel="noopener noreferrer">
                  <img src={gitIcon} alt="" className="h-5 w-5" />
                  GitHub
                </a>
              </Button>
            </div>
            <div className={linkButtons}>
              <Button asChild variant="outline" className={buttonDetails}>
                <a href="https://www.linkedin.com/in/justin-ott/" target="_blank" rel="noopener noreferrer">
                  <img src={linkedInIcon} alt="" className="h-5 w-5" />
                  LinkedIn
                </a>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <p className="text-lg max-w-xl text-center">
        Get in touch! Fill out the form below and I'll get back to you soon.
      </p>
      <div className="flex justify-center mt-4">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="lg" className={buttonDetails}>Send Me a Message</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Contact Me</DialogTitle>
              <DialogDescription>
                Fill out the form below and I'll get back to you as soon as possible.
              </DialogDescription>
            </DialogHeader>
            <ContactForm onSuccess={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}