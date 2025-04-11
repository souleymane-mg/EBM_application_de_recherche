import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  TextInput,
  Select,
  Button,
  Alert,
  Spinner,
  Modal,
  Tooltip
} from 'flowbite-react';
import { HiSearch, HiPlus, HiDownload, HiTrash, HiPencil } from 'react-icons/hi';
import api from '../services/api';
import DocumentCard from '../components/DocumentCard';

const HomePage = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [docType, setDocType] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getAllDocuments();
      setDocuments(data);
    } catch (error) {
      setError('Erreur lors de la récupération des documents');
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await api.searchDocuments(searchQuery, docType);
      setDocuments(results);
    } catch (error) {
      setError('Erreur lors de la recherche');
      console.error('Erreur de recherche:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await api.deleteDocument(docId);
      fetchDocuments();
      setShowDeleteModal(false);
    } catch (error) {
      setError('Erreur lors de la suppression du document');
      console.error('Erreur de suppression:', error);
    }
  };

  const handleDownload = async (docId) => {
    try {
      const blob = await api.downloadDocument(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document-${docId}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError('Erreur lors du téléchargement');
      console.error('Erreur de téléchargement:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Documents disponibles</h2>
        <Button onClick={() => navigate('/add')} className="bg-purple-600 hover:bg-purple-700">
          <HiPlus className="mr-2 h-5 w-5" />
          Ajouter un document
        </Button>
      </div>

      <Card className="mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <TextInput
            icon={HiSearch}
            placeholder="Rechercher..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="w-full md:w-48"
          >
            <option value="">Tous les types</option>
            <option value="PDF">PDF</option>
            <option value="DOCX">DOCX</option>
            <option value="TXT">TXT</option>
          </Select>
          <Button onClick={handleSearch}>
            <HiSearch className="mr-2 h-5 w-5" />
            Rechercher
          </Button>
        </div>
      </Card>

      {error && (
        <Alert color="failure" className="mb-4">
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="flex justify-center">
          <Spinner size="xl" />
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(
            documents.reduce((acc, doc) => {
              const category = doc.doc_type || 'Autres';
              if (!acc[category]) acc[category] = [];
              acc[category].push(doc);
              return acc;
            }, {})
          ).map(([category, docs]) => (
            <div key={category} className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-800 dark:text-white">{category}</h3>
                <div className="flex items-center">
                  <Button
                    size="xs"
                    color="gray"
                    className="flex items-center gap-1"
                    onClick={() => navigate('/add', { state: { preselectedType: category } })}
                  >
                    <HiPlus className="h-3 w-3" />
                    Ajouter
                  </Button>
                </div>
              </div>
              <div className="relative">
                <div className="flex overflow-x-auto pb-4 gap-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
                  {docs.map((doc) => (
                    <div key={doc.doc_id} className="flex-shrink-0">
                      <DocumentCard 
                        document={doc} 
                        onDelete={() => {
                          setSelectedDoc(doc);
                          setShowDeleteModal(true);
                        }}
                        onDownload={() => handleDownload(doc.doc_id)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        show={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        popup
        size="md"
      >
        <Modal.Header />
        <Modal.Body>
          <div className="text-center">
            <HiTrash className="mx-auto mb-4 h-14 w-14 text-red-500" />
            <h3 className="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
              Êtes-vous sûr de vouloir supprimer ce document ?
              <div className="mt-2 font-semibold">{selectedDoc?.doc_name}</div>
            </h3>
            <div className="flex justify-center gap-4">
              <Button
                color="red"
                onClick={() => handleDelete(selectedDoc?.doc_id)}
              >
                Oui, supprimer
              </Button>
              <Button
                color="gray"
                onClick={() => setShowDeleteModal(false)}
              >
                Annuler
              </Button>
            </div>
          </div>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default HomePage; 