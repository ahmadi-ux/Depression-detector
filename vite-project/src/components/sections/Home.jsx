// Home Section introducing me seen when loading the site
// This might be to simple but I did not want to add a photo to this page 
// and everything else is in the site already
export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-orange-100 p-4">
      <h1 className="text-5xl font-bold mb-4">
        Hello, I'm Justin Ott
      </h1>
      <p className="text-lg text-gray-700 max-w-xl text-center">
        I am a computer science student at GVSU interested in software development,
        networking, and building interactive web applications.
      </p>
    </div>
  )
}