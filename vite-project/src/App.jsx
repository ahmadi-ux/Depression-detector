import { Routes, Route } from 'react-router'
import Navigation from './components/sections/Navigation'
import Home from './components/sections/Home'
import Experience from './components/sections/Experience'
import Skills from './components/sections/Skills'
import Projects from './components/sections/Projects'
import ProjectDetails from './components/projectFolder/ProjectDetails'
import Aboutme from './components/sections/Aboutme'
import DataUpload from './components/sections/DataUpload'
import AdminLogin from './components/sections/AdminLogin'
import AdminDashboard from './components/sections/AdminDashboard'
import DataInput from './components/sections/Input'
import DataOutput from './components/sections/Output'

/** Main Application Component
 * - Sets up routing for different sections and pages
 * - Includes Navigation bar and section components
 */
function App() {
  return (
    <>
      <Navigation />
      <div className="absolute left-8 bg-blue-100 top-1/2 transform -translate-y-1/2 text-6xl opacity-20"></div>
      <div className="artistic-column right" /> {/* Additional spacer for fixed nav */}
      <Routes>
        <Route path="/" element={
          <>
            <div id="home">
              <Home />
            </div>
            <div id="DataUpload">
              <DataUpload />
            </div>
            {/*
            <div id="DataOutput">
              <DataOutput />
            </div>
            */}

            {/* <div id="experience">
              <Experience />
            </div> */}
            {/* <div id="skills">
              <Skills />
            </div> */}
            {/* <div id="projects">
              <Projects />
            </div> */}
            {/* <div id="aboutme">
              <Aboutme />
            </div> */}
          </>
        } />
        <Route path="/projects/:id" element={<ProjectDetails />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
      </Routes>
    </>
  )
}

export default App