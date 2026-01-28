import { useForm } from "react-hook-form";
import { collection, addDoc } from "firebase/firestore";
import { db } from "../firebase/app";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "./ui/form";

/** Contact Form Component
 * - Uses react-hook-form for form state management and validation
 * - Saves files to Firestore as Base64 encoded data
 * - No CORS issues - everything stays within Firebase ecosystem
*/
export default function ContactForm({ onSuccess }) {
  const form = useForm({
    defaultValues: {
      file: null,
    },
  });

  const onSubmit = async (values) => {
    console.log("SUBMIT FIRED", values);
    console.log("FILE:", values.file, values.file instanceof File);

    try {
      if (!values.file) {
        alert("Please select a file");
        return;
      }

      console.log("Reading file as Base64...");
      
      // Convert file to Base64 using a safe method
      const fileData = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(values.file);
      });

      // fileData is already in "data:image/png;base64,..." format
      // Extract just the base64 part
      const base64String = fileData.split(',')[1];

      console.log("Saving file to Firestore...");
      
      // Save to Firestore with Base64 encoded file
      await addDoc(collection(db, "submissions"), {
        fileName: values.file.name,
        fileType: values.file.type,
        fileSize: values.file.size,
        fileData: base64String,
        timestamp: new Date(),
      });

      form.reset({ file: null });
      alert("File saved successfully!");
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error("Upload error:", error);
      alert(`Error: ${error.message}`);
    }
  };

  // Contact Form UI
  return (
    <div className="w-full">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="file"
            rules={{ required: "Please upload a file" }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Upload File</FormLabel>
                <FormControl>
                  <Input
                    type="file"
                    accept=".pdf,.doc,.docx,.png,.jpg,.csv,.txt,.xlsx"
                    onChange={(e) => field.onChange(e.target.files[0])}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Submitting..." : "Send Message"}
          </Button>
        </form>
      </Form>
    </div>
  );
}