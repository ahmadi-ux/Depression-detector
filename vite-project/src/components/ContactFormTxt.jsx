import { useForm } from "react-hook-form";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import {
  Form, FormControl, FormField,
  FormItem, FormLabel, FormMessage,
} from "./ui/form";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
console.log("API_URL:", API_URL);

/**
 * Depression Detector Form Component
 * - Text input via textarea
 * - Backend processes with LLMs
 * - Returns PDF report for download
 */
export default function DepressionDetectorForm({ onSuccess, llm }) {
  const form = useForm({
    defaultValues: {
      text: "",
    },
  });

  const onSubmit = async (values) => {
    try {
      const formData = new FormData();
      formData.append("llm", llm);
      formData.append("text", values.text);

      // Send to backend - returns immediately with job ID
      console.log("Submitting text...");
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

      // Poll for job completion
      let isComplete = false;
      let pollCount = 0;
      const maxPolls = 600; // 10 minutes max

      while (!isComplete && pollCount < maxPolls) {
        // Wait 1 second before polling
        await new Promise(r => setTimeout(r, 1000));
        pollCount++;

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
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${jobId.substring(0, 8)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            isComplete = true;
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
        throw new Error('Processing timeout - took longer than 10 minutes');
      }

      form.reset({ text: "" });
      alert("✓ Report generated and downloaded successfully!");
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
            name="text"
            rules={{
              required: "Please enter text to analyze",
              minLength: {
                value: 10,
                message: "Text must be at least 10 characters",
              },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Text to Analyze</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Enter text for depression analysis... (e.g., journal entries, messages, etc.)"
                    className="resize-none min-h-[200px]"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
                <p className="text-sm text-gray-500 mt-2">
                  Minimum 10 characters required. The system will analyze linguistic signals related to depression.
                </p>
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "Analyzing..." : "Analyze & Generate Report"}
          </Button>
        </form>
      </Form>
    </div>
  );
}