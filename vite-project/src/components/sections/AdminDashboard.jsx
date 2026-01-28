import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { collection, getDocs, query, orderBy, deleteDoc, doc } from "firebase/firestore";
import { signOut, onAuthStateChanged } from "firebase/auth";
import { db, auth } from "../../firebase/app";
import { Button } from "../ui/button";
import { LogOut, Mail, User, Calendar, Trash2, Loader2 } from "lucide-react";

export default function AdminDashboard() {
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);
    const [deleting, setDeleting] = useState(null);
    const navigate = useNavigate();

    /** Handles authentication state
     * - If user is logged in, fetch submissions
     * - If not logged in, redirect to login page
    */
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            if (currentUser) {
                setUser(currentUser);
                fetchSubmissions();
            } else {
                navigate("/admin/login");
            }
        });

        return () => unsubscribe();
    }, [navigate]);

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

    /** Handles logouts
     * - Signs out the user from Firebase Auth
     * - Redirects to login page
     */
    const handleLogout = async () => {
        try {
            await signOut(auth);
            navigate("/admin/login");
        } catch (error) {
            console.error("Logout error:", error);
            alert("Failed to logout");
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
                            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
                            <p className="text-sm text-gray-600 mt-1">
                                Logged in as: {user?.email}
                            </p>
                        </div>
                        <Button onClick={handleLogout} variant="outline" className="gap-2 rounded-xl shadow-md hover:scale-105 transition-transform">
                            <LogOut className="h-4 w-4" />
                            Logout
                        </Button>
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
                                            <User className="h-4 w-4 text-gray-500" />
                                            <span className="font-semibold text-lg">
                                                {submission.name}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-gray-600 mb-2">
                                            <Mail className="h-4 w-4" />
                                            <a
                                                href={`mailto:${submission.email}`}
                                                className="hover:underline"
                                            >
                                                {submission.email}
                                            </a>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                            <Calendar className="h-4 w-4" />
                                            <span>{formatDate(submission.timestamp)}</span>
                                        </div>
                                    </div>
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
                                <div className="border-t pt-4">
                                    <p className="text-sm font-medium text-gray-700 mb-2">
                                        Message:
                                    </p>
                                    <p className="text-gray-800 whitespace-pre-wrap">
                                        {submission.message}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}