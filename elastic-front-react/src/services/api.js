import axios from 'axios';

const API_URL = 'http://localhost:5000';

// Configuration d'Axios pour gérer les erreurs
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('Erreur API:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

const api = {
  // Récupérer tous les documents
  getAllDocuments: async () => {
    try {
      const response = await axios.get(`${API_URL}/documents`);
      return response.data.map(doc => ({
        ...doc,
        title: doc.doc_name, // Pour la compatibilité avec l'interface existante
        content: doc.doc_content // Pour la compatibilité avec l'interface existante
      }));
    } catch (error) {
      console.error('Erreur lors de la récupération des documents:', error);
      throw error;
    }
  },

  // Ajouter un document
  addDocument: async (formData) => {
    try {
      const response = await axios.post(`${API_URL}/documents`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'ajout du document:', error);
      throw error;
    }
  },

  // Rechercher des documents
  searchDocuments: async (query, docType) => {
    try {
      const response = await axios.get(`${API_URL}/search`, {
        params: { query, doc_type: docType }
      });
      return response.data.documents || [];
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
      throw error;
    }
  },

  // Supprimer un document
  deleteDocument: async (docId) => {
    try {
      await axios.delete(`${API_URL}/documents/${docId}`);
      return true;
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      throw error;
    }
  },

  // Télécharger un document
  downloadDocument: async (docId) => {
    try {
      const response = await axios.get(`${API_URL}/documents/${docId}/download`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      throw error;
    }
  }
};

export default api; 