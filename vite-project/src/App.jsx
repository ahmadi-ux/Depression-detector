import { Routes, Route } from 'react-router'
import { useState } from 'react'
import Navigation from './components/sections/Navigation'
import Home from './components/sections/Home'
import DataUpload from './components/sections/DataUpload'
import DataUploadTxt from './components/sections/DataUploadTxt'
import { SuccessModal } from './components/SuccessModal'

/** Main Application Component
 * - Sets up routing for different sections and pages
 * - Includes Navigation bar and section components
 * - Manages SuccessModal state at the app level so it persists across form changes
 */
function App() {
  const [showModal, setShowModal] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [modalMessage, setModalMessage] = useState("");

  const handleShowResult = (classification, message) => {
    setPrediction(classification);
    setModalMessage(message);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  return (
    <>
      <Navigation />
      <div className="absolute left-8 bg-blue-100 top-1/2 transform -translate-y-1/2 text-6xl opacity-20"></div>
      <div className="artistic-column right" /> {/* Additional spacer for fixed nav */}
      
      {/* SuccessModal at app level so it persists across form unmounts */}
      <SuccessModal 
        show={showModal}
        message={modalMessage}
        classification={prediction}
        onClose={handleCloseModal}
      />
      
      <Routes>
        <Route path="/" element={
          <>
            <div id="home">
              <Home />
            </div>
            <div id="DataUpload">
              <DataUpload onShowResult={handleShowResult} />
            </div>
            <div id="DataUploadTxt">
              <DataUploadTxt onShowResult={handleShowResult} />
            </div>
          </>
        } />
      </Routes>
    </>
  )
}

export default App