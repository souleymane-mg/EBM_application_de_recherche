import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Label, TextInput, Select, FileInput, Button, Alert } from 'flowbite-react';
import { HiArrowLeft, HiUpload } from 'react-icons/hi';
import api from '../services/api';

const AddDocumentPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    doc_id: '',
    doc_name: '',
    doc_type: '',
    file: null
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [documentTypes, setDocumentTypes] = useState([
    'CV',
    'Fiche de poste',
    'Évaluation annuelle',
    'Rapport',
    'Autre'
  ]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.file) {
      setError('Veuillez sélectionner un fichier');
      return;
    }

    if (!formData.doc_name || !formData.doc_type) {
      setError('Le nom et le type du document sont obligatoires');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const formDataToSend = new FormData();
      formDataToSend.append('file', formData.file);
      formDataToSend.append('doc_id', formData.doc_id);
      formDataToSend.append('doc_name', formData.doc_name);
      formDataToSend.append('doc_type', formData.doc_type);

      await api.addDocument(formDataToSend);
      navigate('/');
    } catch (error) {
      setError('Erreur lors de l\'ajout du document');
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const fileExt = file.name.split('.').pop().toUpperCase();
      if (!['PDF', 'DOCX'].includes(fileExt)) {
        setError('Format de fichier non autorisé. Seuls PDF et DOCX sont acceptés');
        return;
      }
      setFormData({ ...formData, file });
      setError('');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Button
        color="gray"
        onClick={() => navigate('/')}
        className="mb-4"
      >
        <HiArrowLeft className="mr-2 h-5 w-5" />
        Retour
      </Button>

      <Card className="max-w-2xl mx-auto">
        <h5 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white mb-4">
          Ajouter un nouveau document
        </h5>

        {error && (
          <Alert color="failure" className="mb-4">
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <Label htmlFor="doc_id" value="ID du document" />
            <TextInput
              id="doc_id"
              type="text"
              value={formData.doc_id}
              onChange={(e) => setFormData({ ...formData, doc_id: e.target.value })}
              placeholder="Laissez vide pour générer automatiquement"
            />
            <p className="mt-1 text-sm text-gray-500">
              Cet ID sera utilisé dans le nom du fichier stocké
            </p>
          </div>

          <div>
            <Label htmlFor="doc_name" value="Nom du document" required />
            <TextInput
              id="doc_name"
              type="text"
              value={formData.doc_name}
              onChange={(e) => setFormData({ ...formData, doc_name: e.target.value })}
              required
            />
          </div>

          <div>
            <Label htmlFor="doc_type" value="Type de document" required />
            <Select
              id="doc_type"
              value={formData.doc_type}
              onChange={(e) => setFormData({ ...formData, doc_type: e.target.value })}
              required
            >
              <option value="">Sélectionnez un type</option>
              {documentTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </Select>
          </div>

          <div>
            <Label htmlFor="file" value="Fichier (PDF ou DOCX uniquement)" required />
            <FileInput
              id="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Formats acceptés : PDF, DOCX
            </p>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="mt-4"
          >
            {loading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                En cours...
              </div>
            ) : (
              <>
                <HiUpload className="mr-2 h-5 w-5" />
                Ajouter le document
              </>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default AddDocumentPage; 