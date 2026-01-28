const TimelineLine = () => (
  // Each section is only as big as the text so the dots line up with the "title" of each section
  // (this sucked to make but I really liked how it looked from the inspiration site)
  <div className="relative w-6 flex-shrink-0">
    <div className="absolute top-3 -left-7 w-4 h-4 bg-black rounded-full shadow-sm"></div> {/* Top dot */}
    <div className="w-px h-full bg-gray-400"></div> {/* The Line */}
  </div>);

/** Experience Section with timeline of key milestones
 * - Downloadable resume button
 * - Timeline of experiences (this sucked to make but I really liked how it looked from the inspiration site)
*/
export default function Experience() {
  return (
    <div className="h-auto flex flex-col items-center justify-center bg-blue-100 p-4 px-8 py-32">
      <h2 className="text-5xl font-bold mb-6">Experience</h2>
      {/* Resume Download Button*/}
      <button>
        <div className="w-fit h-fit text-2xl font-bold bg-blue-300 mb-12 flex rounded-xl items-center justify-center p-6 hover:bg-blue-400 transition-colors shadow-lg">
          <a href="/downloads/Justin Ott Resume.pdf" download="Justin Ott Resume.pdf" className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-9">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span>Download Resume</span>
          </a>
        </div>
      </button>

      {/* Timeline Container */}
      <div className="w-full max-w-xl flex flex-col">

        {/* Experience Item 2 */}
        <div className="flex gap-6">
          {/* Vertical Line Column */}
          <TimelineLine />
          {/* Content Column */}
          <div className="pb-6">
            <h3 className="text-xl md:text-2xl font-bold tracking-wide">
              Started Applying for Internships
            </h3>
            <hr className="border-black my-2"></hr>
            <time className="text-xs md:text-sm font-bold tracking-wide uppercase text-gray-500">
              September 2024
            </time>
            <p className="text-lg text-gray-700 mt-2">
              After starting CIS 290 at GVSU I started applying for software development internships and have yet to receive any positions.
            </p>
          </div>
        </div>

        {/* Experience Item 2 */}
        <div className="flex gap-6">
          {/* Vertical Line Column */}
          <TimelineLine />
          {/* Content Column */}
          <div className="pb-6">
            <h3 className="text-xl md:text-2xl font-bold tracking-wide">
              Started Computer Science Coursework
            </h3>
            <hr className="border-black my-2"></hr>
            <time className="text-xs md:text-sm font-bold tracking-wide uppercase text-gray-500">
              August 2022
            </time>
            <p className="text-lg text-gray-700 mt-2">
              My programming journey began at GVSU learning Python.
            </p>
          </div>
        </div>

        {/* Experience Item 3 */}
        <div className="flex gap-6">
          {/* Vertical Line Column */}
          <TimelineLine />
          {/* Content Column */}
          <div className="pb-6">
            <h3 className="text-xl md:text-2xl font-bold tracking-wide">
              Introduced to Programming
            </h3>
            <hr className="border-black my-2"></hr>
            <time className="text-xs md:text-sm font-bold tracking-wide uppercase text-gray-500">
              August 2021
            </time>
            <p className="text-lg text-gray-700 mt-2">
              Started learning the basics of programming in my highschool AP Computer Science Principles class.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
