import { useState, useEffect } from "react";
import { collection, getDocs, query, orderBy, deleteDoc, doc } from "firebase/firestore";
import { db } from "../../firebase/app";
import { Button } from "../ui/button";
import { Mail, FileText, Calendar, Trash2, Loader2, Eye, EyeOff } from "lucide-react";

// CSV Preview Component
function CSVPreview({ fileURL }) {
    const [content, setContent] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchCSV = async () => {
            try {
                const response = await fetch(fileURL);
                const text = await response.text();
                const lines = text.split('\n').slice(0, 50).join('\n');
                setContent(lines);
            } catch (err) {
                setError("Failed to load CSV preview");
            }
        };
        fetchCSV();
    }, [fileURL]);

    return (
        <div>
            {error ? (
                <p className="text-red-600">{error}</p>
            ) : (
                <pre className="overflow-x-auto whitespace-pre-wrap break-words bg-gray-50 p-3 rounded text-xs">
                    {content}
                </pre>
            )}
        </div>
    );
}

export default function AdminDashboard() {
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState(null);
    const [expandedFile, setExpandedFile] = useState(null);

    // Fetch submissions on component mount
    useEffect(() => {
        fetchSubmissions();
    }, []);

    /** Fetches contact form submissions from Firestore 
     * - Orders by timestamp descending
    */
    const fetchSubmissions = async () => {
        try {
            const q = query(collection(db, "submissions"), orderBy("timestamp", "desc"));
            const querySnapshot = await getDocs(q);
            // Actually maps the firestore documents into JS objects
            const data = querySnapshot.docs.map((doc) => ({
                id: doc.id,
                ...doc.data(),
            }));
            setSubmissions(data);
        } catch (error) {
            console.error("Error fetching submissions:", error);
            alert("Failed to load submissions");
        } finally {
            setLoading(false);
        }
    };

    /** Handles deleting a submission 
     * - Prompts for confirmation
     * - Deletes the submission from Firestore
     * - Updates local state
    */
    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this submission?")) {
            return;
        }

        setDeleting(id);
        try {
            await deleteDoc(doc(db, "submissions", id));
            setSubmissions(submissions.filter((sub) => sub.id !== id));
        } catch (error) {
            console.error("Error deleting submission:", error);
            alert("Failed to delete submission");
        } finally {
            setDeleting(null);
        }
    };

    /** Formats Firestore timestamp to readable string */
    const formatDate = (timestamp) => {
        if (!timestamp) return "N/A";
        const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
        return date.toLocaleString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    // Adds loading spinner if needed
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
            </div>
        );
    }

    // Dashboard UI
    return (
        <div className="min-h-screen bg-blue-100">
            <header className="bg-orange-100 shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold">File Submissions</h1>
                            <p className="text-sm text-gray-600 mt-1">
                                View all uploaded files and data
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold">
                        Contact Form Submissions ({submissions.length})
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                        Manage and review all contact form submissions
                    </p>
                </div>

                {submissions.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            No submissions yet
                        </h3>
                        <p className="text-gray-600">
                            Contact form submissions will appear here
                        </p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {submissions.map((submission) => (
                            <div
                                key={submission.id}
                                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <FileText className="h-4 w-4 text-gray-500" />
                                            <span className="font-semibold text-lg">
                                                {submission.fileName || "Unnamed File"}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                            <Mail className="h-4 w-4" />
                                            <span>{submission.fileType || "N/A"}</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                            <Calendar className="h-4 w-4" />
                                            <span>{formatDate(submission.timestamp)}</span>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            onClick={() => setExpandedFile(expandedFile === submission.id ? null : submission.id)}
                                            variant="outline"
                                            size="sm"
                                            className="gap-2"
                                        >
                                            {expandedFile === submission.id ? (
                                                <><EyeOff className="h-4 w-4" /> Hide</>
                                            ) : (
                                                <><Eye className="h-4 w-4" /> View</>
                                            )}
                                        </Button>
                                        <Button
                                            onClick={() => handleDelete(submission.id)}
                                            variant="ghost"
                                            size="sm"
                                            disabled={deleting === submission.id}
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        >
                                            {deleting === submission.id ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Trash2 className="h-4 w-4" />
                                            )}
                                        </Button>
                                    </div>
                                </div>
                                <div className="border-t pt-4">
                                    <p className="text-sm font-medium text-gray-700 mb-2">
                                        File Details:
                                    </p>
                                    <p className="text-gray-800 mb-3">
                                        <strong>Size:</strong> {(submission.fileSize / 1024).toFixed(2)}KB
                                    </p>
                                    {submission.fileURL && (
                                        <a
                                            href={submission.fileURL}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:underline text-sm"
                                        >
                                            Download File
                                        </a>
                                    )}
                                </div>
                                {expandedFile === submission.id && submission.fileURL && (
                                    <div className="border-t pt-4 mt-4">
                                        <p className="text-sm font-medium text-gray-700 mb-3">Preview:</p>
                                        <div className="bg-gray-100 rounded-lg overflow-hidden">
                                            {submission.fileType?.includes('pdf') ? (
                                                <iframe
                                                    src={submission.fileURL}
                                                    style={{
                                                        width: '100%',
                                                        height: '600px',
                                                        border: 'none',
                                                    }}
                                                    title="PDF Viewer"
                                                />
                                            ) : submission.fileType?.includes('image') ? (
                                                <img
                                                    src={submission.fileURL}
                                                    alt="File preview"
                                                    style={{
                                                        width: '100%',
                                                        maxHeight: '600px',
                                                        objectFit: 'contain',
                                                    }}
                                                />
                                            ) : submission.fileType?.includes('csv') || submission.fileType?.includes('text') ? (
                                                <div className="p-4 bg-white text-sm">
                                                    <p className="text-gray-600 mb-3">Preview (first 50 lines):</p>
                                                    <CSVPreview fileURL={submission.fileURL} />
                                                </div>
                                            ) : submission.fileType?.includes('presentation') || submission.fileType?.includes('powerpoint') ? (
                                                <div className="p-4 bg-white">
                                                    <p className="text-gray-600 mb-2">PPTX files cannot be previewed in browser</p>
                                                    <a
                                                        href={submission.fileURL}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-600 hover:underline"
                                                    >
                                                        Open in new tab
                                                    </a>
                                                </div>
                                            ) : submission.fileType?.includes('word') || submission.fileType?.includes('document') ? (
                                                <div className="p-4 bg-white">
                                                    <p className="text-gray-600 mb-2">Document files cannot be previewed in browser</p>
                                                    <a
                                                        href={submission.fileURL}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-600 hover:underline"
                                                    >
                                                        Download to view
                                                    </a>
                                                </div>
                                            ) : (
                                                <div className="p-4 text-gray-600">
                                                    Preview not available for {submission.fileType || 'this'} files. 
                                                    <a
                                                        href={submission.fileURL}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-600 hover:underline ml-2"
                                                    >
                                                        Download instead
                                                    </a>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}