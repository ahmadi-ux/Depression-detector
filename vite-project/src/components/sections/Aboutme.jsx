export default function Aboutme() {
  return (
    <div className="h-auto flex flex-col items-center justify-center bg-green-100 p-4 px-8 py-32"
    // Background gif that I thought about using
    // style={{ backgroundImage: 'url(/LegoLoop.gif)', backgroundSize: 'cover', backgroundPosition: 'center' }}
    >
      <h2 className="text-5xl font-bold mb-6">About Me</h2>
      { /* Currently 3 sections of information about my programming experience */}
      <div className="max-w-4xl w-full space-y-8">
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-2xl font-semibold mb-3 text-green-700">My Journey</h3>
          <p className="text-lg text-gray-700">
            I started learning the basics of programming during my senior year of highschool
            in my Computer Science Principles AP class. At this point I was still torn between 
            going for some sort of engineering degree or majoring in another field. After taking CSP, I fell in love
            with programming and decided to pursue a degree in Computer Science. I ended up choosing GVSU
            due to its large scholarships and computer science program. During my time at GVSU, I have learned
            a lot about not only different languages, but also how to work with a team and manage 
            my projects and time.
          </p>
        </div>  
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-2xl font-semibold mb-3 text-green-700">Where I am Now</h3>
          <p className="text-lg text-gray-700">
            Currently I have finished all of the required coursework for both my degree in computer science as 
            well as minors in mathematics and cybersecurity. My main areas of interest are software 
            development and web development, which you can see in the projects that I have posted both on this site 
            and on my GitHub. I have yet to really dive into more software development focused 
            personal projects. Recently, I have been leaning more into the web development and front-end side of things as I really 
            enjoy building interactive web applications, and web games and then being able to interact with what I built.
          </p>
      </div>
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-2xl font-semibold mb-3 text-green-700">What I am Looking For</h3>
          <p className="text-lg text-gray-700">
            I am currently missing the internship requirement for my degree, and have been
            actively applying to internships. I am really open to any internship or job 
            opportunities that come my way in the field of computer science. As, even if 
            I am not offered a full-time postion with the company after the internship, I know that I 
            will learn a lot from the experience, which I will be able to carry and apply to future opportunities.
          </p>
      </div>
    </div>
    </div>
  )
}