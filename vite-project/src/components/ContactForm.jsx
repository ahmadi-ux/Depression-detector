import { useForm } from "react-hook-form";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ResultAnimation } from "./ResultAnimation";
import { useState } from "react";
import {
  Form, FormControl, FormField, 
  FormItem, FormLabel, FormMessage,
} from "./ui/form";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
console.log("API_URL:", API_URL);
/**
 * Depression Detector Form Component
 * - Upload file (PDF, CSV, TXT)
 * - Backend processes with llms
 * - Returns PDF report for download
 * - Triggers animations based on depression classification
 */
export default function ContactForm({ onSuccess, llm, prompt, onShowResult }) {
  const [prediction, setPrediction] = useState(null);
  const form = useForm({
    defaultValues: {
      files: [],
    },
  });

  const onSubmit = async (values) => {
    try {
      if (!values.files || values.files.length === 0) {
        alert("Please select at least one file");
        return;
      }

      const files = values.files;
      console.log(`Processing ${files.length} file(s) with ${prompt} prompt...`);

      const formData = new FormData();
      formData.append("llm", llm.toLowerCase());
      formData.append("prompt", prompt);  // Add prompt type
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Send to backend - returns immediately with job ID
      console.log("Submitting file...");
      const uploadResponse = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(errorData.error || `Upload failed: ${uploadResponse.statusText}`);
      }

      const uploadData = await uploadResponse.json();
      const jobId = uploadData.job_id;
      console.log(`✓ Job started: ${jobId}`);
      
      // alert(`Processing started... Please wait.\nJob ID: ${jobId}`);

      // Poll for job completion
      let isComplete = false;
      let pollCount = 0;
      const maxPolls = 3600; // 60 minutes max (1 poll per second)

      while (!isComplete && pollCount < maxPolls) {
        // Wait 1 second before polling
        await new Promise(r => setTimeout(r, 1000));
        pollCount++;
        console.log(`Polling attempt ${pollCount}`);

        try {
          console.log(`[Poll ${pollCount}] Checking status for job ${jobId.substring(0, 8)}...`);
          const statusResponse = await fetch(`${API_URL}/api/job/${jobId}`);
          
          if (!statusResponse.ok) {
            const errorData = await statusResponse.json();

            // Job failed permanently – stop polling
            if (statusResponse.status === 400 && errorData.status === "error") {
              throw new Error(`Processing failed: ${errorData.error}`);
            }

            // Temporary error – keep polling
            throw new Error("Temporary polling error");
          }


          // Success response - could be PDF or JSON status
          const contentType = statusResponse.headers.get('content-type');
          
          if (contentType && contentType.includes('application/pdf')) {
            // PDF is ready!
            console.log("✓ PDF ready! Downloading...");
            const blob = await statusResponse.blob();
            const url = window.URL.createObjectURL(blob);
            // Try to get filename from Content-Disposition header
            let filename = "report.pdf";
            const disposition = statusResponse.headers.get('content-disposition');
            if (disposition && disposition.includes('filename=')) {
              const match = disposition.match(/filename="?([^";]+)"?/);
              if (match && match[1]) {
                filename = match[1];
              }
            }
            const a = document.createElement('a');
            a.href = url;
            a.download = `Depression_Report_${filename}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            isComplete = true;
            
            // Extract depression classification from response headers
            const classification = statusResponse.headers.get('X-Depression-Classification');
            if (classification) {
              console.log(`✓ Classification extracted: ${classification}`);
              // Call parent handler immediately with the classification (don't wait for state)
              if (onShowResult) {
                onShowResult(classification, "✓ Report generated and downloaded successfully!");
              }
            } else {
              console.log("⚠ No classification header found");
            }
            
            console.log("✓ Download complete!");
          } else {
            // Still processing - parse JSON status
            const statusData = await statusResponse.json();
            console.log(`Status: ${statusData.status} | Progress: ${statusData.progress}%`);
          }
        } catch (pollError) {
          console.error(`Poll error: ${pollError.message}`);
            if (pollError.message.startsWith("Processing failed")) {
            throw pollError; // stop everything
          }
        }
      }

      if (!isComplete) {
        throw new Error('Processing timeout - took longer than 60 minutes');
      }

      form.reset({ file: null });
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error("Error:", error);
      alert(`❌ Error: ${error.message}`);
    }
  };

  return (
    <div className="w-full">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="files"
            rules={{ required: "Please select at least one file to analyze" }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Upload Documents for Analysis</FormLabel>
                <FormControl>
                  <Input
                    type="file"
                    accept=".pdf,.csv,.txt,.doc,.docx"
                    multiple
                    onChange={(e) => field.onChange(Array.from(e.target.files))}
                  />
                </FormControl>
                <FormMessage />
                <p className="text-sm text-gray-500 mt-2">
                  Supported formats: PDF, CSV, TXT, DOC, DOCX
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