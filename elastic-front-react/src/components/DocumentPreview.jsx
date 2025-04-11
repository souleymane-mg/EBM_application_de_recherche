import React, { useState } from 'react';

const DocumentPreview = ({ document }) => {
  const [error, setError] = useState(null);

  // Normaliser la structure du document pour gérer à la fois doc_format et format, doc_name et name, etc.
  const docFormat = document.doc_format || document.format || (document.title?.endsWith('.pdf') ? 'PDF' : 'DOCX');
  const docName = document.doc_name || document.name || document.title || 'Document';
  const docId = document.doc_id || document.id || Math.random().toString(36).substring(7);

  const getRandomColor = (id) => {
    // Générer une couleur basée sur l'ID du document pour qu'elle soit toujours la même pour un document donné
    const hash = String(id).split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);
    
    const h = Math.abs(hash % 360);
    return `hsl(${h}, 70%, 50%)`;
  };

  const getInitial = (name) => {
    return name && name.length > 0 ? name.charAt(0).toUpperCase() : '?';
  };

  const PreviewContainer = ({ children }) => (
    <div 
      className="w-[180px] h-[180px] overflow-hidden bg-white rounded-lg shadow-md"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {children}
    </div>
  );

  if (error) {
    return (
      <PreviewContainer>
        <span className="text-sm text-red-500 text-center px-2">{error}</span>
      </PreviewContainer>
    );
  }

  // Pour les PDF, on affiche une icône stylisée
  if (docFormat === 'PDF') {
    const bgColor = getRandomColor(docId);
    const initial = getInitial(docName);

    return (
      <PreviewContainer>
        <div className="w-full h-full p-4 flex flex-col items-center justify-center">
          <div 
            className="w-32 h-40 relative flex items-center justify-center rounded-md shadow-lg mb-2"
            style={{ backgroundColor: bgColor }}
          >
            {/* Corner fold */}
            <div 
              className="absolute top-0 right-0 w-0 h-0 border-l-[20px] border-b-[20px]"
              style={{ 
                borderLeftColor: 'rgba(255, 255, 255, 0.3)', 
                borderBottomColor: 'transparent'
              }}
            ></div>
            
            {/* PDF Type */}
            <div className="absolute bottom-2 w-full text-center text-xs text-white font-bold">
              {docFormat}
            </div>
            
            {/* Document Initial */}
            <span className="text-4xl font-bold text-white">{initial}</span>
          </div>
          
          {/* Document Name (shortened) */}
          <div className="w-full text-center text-xs text-gray-600 truncate">
            {docName}
          </div>
        </div>
      </PreviewContainer>
    );
  }

  // Pour les DOCX
  if (docFormat === 'DOCX') {
    const initial = getInitial(docName);

    return (
      <PreviewContainer>
        <div className="w-full h-full p-4 flex flex-col items-center justify-center">
          <div 
            className="w-32 h-40 relative flex items-center justify-center rounded-md shadow-lg mb-2"
            style={{ backgroundColor: '#4285F4' }}
          >
            {/* Corner fold */}
            <div 
              className="absolute top-0 right-0 w-0 h-0 border-l-[20px] border-b-[20px]"
              style={{ 
                borderLeftColor: 'rgba(255, 255, 255, 0.3)', 
                borderBottomColor: 'transparent'
              }}
            ></div>
            
            {/* DOCX Type */}
            <div className="absolute bottom-2 w-full text-center text-xs text-white font-bold">
              {docFormat}
            </div>
            
            {/* Document Initial */}
            <span className="text-4xl font-bold text-white">{initial}</span>
          </div>
          
          {/* Document Name (shortened) */}
          <div className="w-full text-center text-xs text-gray-600 truncate">
            {docName}
          </div>
        </div>
      </PreviewContainer>
    );
  }

  // Pour les autres types
  return (
    <PreviewContainer>
      <div className="w-full h-full p-4 flex flex-col items-center justify-center">
        <div 
          className="w-32 h-40 relative flex items-center justify-center rounded-md shadow-lg mb-2 bg-gray-200"
        >
          {/* Corner fold */}
          <div 
            className="absolute top-0 right-0 w-0 h-0 border-l-[20px] border-b-[20px]"
            style={{ 
              borderLeftColor: 'rgba(255, 255, 255, 0.5)', 
              borderBottomColor: 'transparent'
            }}
          ></div>
          
          {/* File Type */}
          <div className="absolute bottom-2 w-full text-center text-xs font-bold text-gray-600">
            {docFormat || 'DOC'}
          </div>
          
          {/* Document Icon */}
          <span className="text-4xl text-gray-500">
            {docFormat === 'TXT' ? '📝' : '📄'}
          </span>
        </div>
        
        {/* Document Name (shortened) */}
        <div className="w-full text-center text-xs text-gray-600 truncate">
          {docName}
        </div>
      </div>
    </PreviewContainer>
  );
};

export default DocumentPreview; 