// Home Section introducing me seen when loading the site
// This might be to simple but I did not want to add a photo to this page 
// and everything else is in the site already
export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-orange-100 p-4">
      <h1 className="text-5xl font-bold mb-4">
        Welcome to Depression Detector
      </h1>
      <h2 className="text-2xl mb-6">
        Our goal is to use LLMs to Identify Depression in Students' Writings
      </h2>
      <p className="text-lg text-gray-700 max-w-xl text-center">
        Can LLMs predict self-reported depression and what specific 
        language patterns can be used to identify depression among students in educational contexts?
      </p>
    </div>
  )
}