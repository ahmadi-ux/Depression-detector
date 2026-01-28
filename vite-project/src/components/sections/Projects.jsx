import { Link } from "react-router";
import { ProjectData } from "../projectFolder/ProjectData";

/** Projects Section displaying all projects
 * - Grid layout of project cards
 * - Each card links to detailed project page which opens when clicked
 * - With only two projects so far looks a little empty/small but 
 * - with more projects it will fill out better
 */
export default function Projects() {
  return (
    <div className="h-auto bg-yellow-100 text-black px-8 py-32">
      <h1 className="text-5xl font-bold mb-12 text-center">
        Projects
      </h1>

      <div className="flex justify-center">
        <div className="grid gap-8 grid-cols-2 max-w-2xl">
          {ProjectData.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="group"
            >
              <div
                className="bg-blue-300 rounded-xl p-6 flex flex-col items-center
                transform transition duration-300 hover:scale-105 hover:bg-blue-600"
              >
                <img
                  src={project.icon}
                  alt={project.title}
                  className="w-20 h-20 mb-4"
                />
                <h2 className="text-xl font-semibold text-center">
                  {project.title}
                </h2>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}