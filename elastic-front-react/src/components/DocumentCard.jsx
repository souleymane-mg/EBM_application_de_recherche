import React from 'react';
import { Card, Button, Tooltip } from 'flowbite-react';
import { HiDownload, HiPencil, HiTrash } from 'react-icons/hi';
import DocumentPreview from './DocumentPreview';

const DocumentCard = ({ document, onDelete, onDownload }) => {
  return (
    <Card className="max-w-full h-full w-48 hover:shadow-lg transition-shadow duration-200">
      <div className="flex flex-col h-full p-3">
        <div className="mb-2">
          <DocumentPreview document={document} />
        </div>
        <div className="flex-1">
          <h5 className="text-sm font-bold tracking-tight text-gray-900 dark:text-white mb-1 line-clamp-1">
            {document.title || document.doc_name}
          </h5>
          <p className="text-xs text-gray-700 dark:text-gray-400 line-clamp-2 mb-2">
            {document.content || document.doc_content}
          </p>
        </div>
        <div className="mt-auto">
          <div className="flex justify-end gap-1">
            <Tooltip content="Télécharger" placement="top">
              <Button size="xs" color="gray" pill onClick={onDownload} className="p-1">
                <HiDownload className="h-3 w-3" />
              </Button>
            </Tooltip>
            <Tooltip content="Modifier" placement="top">
              <Button size="xs" color="gray" pill className="p-1">
                <HiPencil className="h-3 w-3" />
              </Button>
            </Tooltip>
            <Tooltip content="Supprimer" placement="top">
              <Button
                size="xs"
                color="gray"
                pill
                onClick={onDelete}
                className="p-1"
              >
                <HiTrash className="h-3 w-3" />
              </Button>
            </Tooltip>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default DocumentCard; 