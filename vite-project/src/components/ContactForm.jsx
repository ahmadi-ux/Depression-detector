import { useForm } from "react-hook-form";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "./ui/form";

/**
 * Depression Detector Form Component
 * - Upload file (PDF, CSV, TXT)
 * - Backend processes with Llama
 * - Returns PDF report for download
 */
export default function ContactForm({ onSuccess }) {
  const form = useForm({
    defaultValues: {
      file: null,
    },
  });

  const onSubmit = async (values) => {
    try {
      if (!values.file) {
        alert("Please select a file");
        return;
      }

      const file = values.file;
      console.log(`Processing ${file.name}...`);
      
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);

      // Send to backend for processing
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Processing failed: ${response.statusText}`);
      }

      // Download the PDF report
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      form.reset({ file: null });
      alert("Report generated and downloaded successfully!");
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error("Error:", error);
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <div className="w-full">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="file"
            rules={{ required: "Please select a file to analyze" }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Upload Document for Analysis</FormLabel>
                <FormControl>
                  <Input
                    type="file"
                    accept=".pdf,.csv,.txt"
                    onChange={(e) => field.onChange(e.target.files[0])}
                  />
                </FormControl>
                <FormMessage />
                <p className="text-sm text-gray-500 mt-2">
                  Supported formats: PDF, CSV, TXT
                </p>
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Analyzing..." : "Analyze & Generate Report"}
          </Button>
        </form>
      </Form>
    </div>
  );
}