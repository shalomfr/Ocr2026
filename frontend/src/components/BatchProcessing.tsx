import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { batchUpload } from '../services/api';
import './BatchProcessing.css';

interface BatchProcessingProps {
  onBack: () => void;
  onNewDocument: () => void;
}

export default function BatchProcessing({ onBack, onNewDocument }: BatchProcessingProps) {
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<any[]>([]);
  const [error, setError] = useState<string>('');

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setError('');

    try {
      const result = await batchUpload(acceptedFiles);
      setUploaded(result.uploaded);

      if (result.errors.length > 0) {
        setError(`${result.errors.length} קבצים נכשלו: ${result.errors.join(', ')}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בהעלאת קבצים');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']
    },
    multiple: true,
    disabled: uploading
  });

  return (
    <div className="card">
      <h2>עיבוד מסמכים נוספים</h2>
      <p>העלה מספר תמונות לעיבוד באצווה (בקרוב...)</p>

      <div className="batch-info">
        <h3>תכונות זמינות</h3>
        <ul>
          <li>✓ המודל מאומן ומוכן לשימוש</li>
          <li>⚠ עיבוד אצווה יהיה זמין בקרוב</li>
          <li>💡 כרגע ניתן לעבד מסמכים אחד אחד</li>
        </ul>
      </div>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div>
            <div className="loading"></div>
            <p>מעלה קבצים...</p>
          </div>
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
            <p>גרור ושחרר תמונות כאן</p>
            <p className="file-types">תמיכה במספר קבצים בו-זמנית</p>
          </div>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {uploaded.length > 0 && (
        <div className="uploaded-list">
          <h3>קבצים שהועלו ({uploaded.length})</h3>
          <div className="uploaded-items">
            {uploaded.map((doc, index) => (
              <div key={index} className="uploaded-item">
                <img src={doc.image_url} alt={doc.filename} />
                <p>{doc.filename}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="action-buttons">
        <button className="button-secondary" onClick={onBack}>
          חזור
        </button>
        <button className="button-primary" onClick={onNewDocument}>
          מסמך חדש
        </button>
      </div>
    </div>
  );
}
