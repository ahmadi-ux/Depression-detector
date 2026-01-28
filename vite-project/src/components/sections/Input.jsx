import axios from "axios";
import React, { useState } from "react";

export default function DataInput() {
  const [selectedFile, setSelectedFile] = useState(null);

  const onFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const onFileUpload = () => {
    if (!selectedFile) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("myFile", selectedFile, selectedFile.name);

    axios
      .post("/api/uploadfile", formData)
      .then((response) => {
        console.log("File uploaded successfully:", response.data);
        alert("File uploaded successfully!");
      })
      .catch((error) => {
        console.error("Error uploading file:", error);
        alert("Error uploading file.");
      });
  };

  const fileData = () => {
    if (selectedFile) {
      return (
        <div className="mt-4">
          <h2 className="text-2xl font-bold">File Details:</h2>
          <p>File Name: {selectedFile.name}</p>
          <p>File Type: {selectedFile.type}</p>
          <p>Last Modified: {new Date(selectedFile.lastModified).toDateString()}</p>
        </div>
      );
    } else {
      return (
        <div className="mt-4">
          <h4>Choose a file before pressing the Upload button</h4>
        </div>
      );
    }
  };

  return (
    <div className="h-auto flex flex-col items-center justify-center bg-pink-100 p-8 py-32">
      <h2 className="text-5xl font-bold mb-8">Data Input</h2>
      
      <input
        type="file"
        onChange={onFileChange}
        className="mb-4"
      />
      
      <button
        onClick={onFileUpload}
        className="text-2xl font-bold bg-blue-300 mb-12 px-6 py-4 rounded-xl hover:bg-blue-400 transition-colors shadow-lg"
      >
        Upload Data
      </button>

      {fileData()}
    </div>
  );
}
