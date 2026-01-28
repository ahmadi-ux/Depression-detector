import { useParams, useNavigate } from "react-router";
import { ProjectData } from "./ProjectData";

export default function ProjectDetail() {
  // Get project ID from URL params
  const { id } = useParams();
  const navigate = useNavigate();
  // Match project by ID
  const project = ProjectData.find((p) => p.id === id);

  const backToProjects = () => {
    // Navigate back to the home page
    navigate('/');
    // Ensure that the page has rendered before scrolling
    setTimeout(() => {
      const element = document.getElementById('projects');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  // Handle case where project is not found
  if (!project) {
    return <div className="text-white p-8">Project not found</div>;
  }

  // Project details UI
  return (
    <div className="min-h-screen bg-gray-600 text-white px-8 py-16">
      <button onClick={backToProjects} className="text-blue-400 hover:underline">
        ← Back to Projects
      </button>

      <div className={`mt-8 grid ${project.demo?.enabled ? "grid-cols-1 lg:grid-cols-2" : "grid-cols-1"} gap-12 max-auto`}>
        {/* Left Column - Project Info */}
        <div>
          <h1 className="text-4xl font-bold mb-4">
            {project.title}
          </h1>

          <p className="text-gray-300 mb-6 whitespace-pre-wrap">
            {project.description}
          </p>

          <h3 className="text-xl font-semibold mb-2">Tech Stack</h3>
          <ul className="flex gap-3 flex-wrap">
            {project.tech.map((tech) => (
              <li
                key={tech}
                className="bg-gray-800 px-3 py-1 mb-2 rounded-lg"
              >
                {tech}
              </li>
            ))}
          </ul>

          <h3 className="text-xl font-semibold mb-2">Links</h3>
          <div className="mt-3 flex gap-4">
            {project.links?.github && (
              <a
                href={project.links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-500"
              >
                GitHub
              </a>
            )}

            {project.links?.demo && (
              <a
                href={project.links.demo}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-500"
              >
                Live Demo
              </a>
            )}
          </div>
        </div>

        {/* Right Column - Live Demo if enabled */}
        {project.demo?.enabled && project.links?.demo && (
          <div className="sticky top-20">
            <h2 className="text-2xl font-semibold mb-4">Live Demo</h2>
            <div className={`${project.demo?.aspectRatio || "aspect-video"} w-full rounded-xl overflow-hidden border border-gray-800`}>
              <iframe
                src={project.links.demo}
                title={`${project.title} Live Demo`}
                className="w-full h-full"
                loading="lazy"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
