import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadImage } from '../services/api';
import './ImageUpload.css';

interface ImageUploadProps {
  onUploadComplete: (documentId: number, imageUrl: string) => void;
}

export default function ImageUpload({ onUploadComplete }: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError('');

    try {
      const result = await uploadImage(file);
      onUploadComplete(result.document_id, result.image_url);
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בהעלאת הקובץ');
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="card">
      <h2>העלאת תמונה</h2>
      <p>העלה תמונת דף כתב יד לעיבוד</p>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div>
            <div className="loading"></div>
            <p>מעלה קובץ...</p>
          </div>
        ) : isDragActive ? (
          <p>שחרר לסרוק הקובץ...</p>
        ) : (
          <div>
            <svg
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p>גרור ושחרר תמונה כאן, או לחץ לבחירת קובץ</p>
            <p className="file-types">PNG, JPG, JPEG, TIF, TIFF, BMP</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error">
          {error}
        </div>
      )}
    </div>
  );
}
