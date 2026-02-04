import { useState, useEffect } from 'react';
import { segmentLines, getLines, transcribeLines } from '../services/api';
import type { Line } from '../types';
import './LineSegmentation.css';

interface LineSegmentationProps {
  documentId: number;
  onComplete: () => void;
  onBack: () => void;
}

export default function LineSegmentation({
  documentId,
  onComplete,
  onBack
}: LineSegmentationProps) {
  const [lines, setLines] = useState<Line[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [transcriptions, setTranscriptions] = useState<{ [lineId: number]: string }>({});

  useEffect(() => {
    loadLines();
  }, [documentId]);

  const loadLines = async () => {
    setLoading(true);
    setError('');

    try {
      const existingLines = await getLines(documentId);

      if (existingLines.length > 0) {
        setLines(existingLines);
        // Initialize transcriptions from existing data
        const initialTrans: { [lineId: number]: string } = {};
        existingLines.forEach(line => {
          if (line.text) {
            initialTrans[line.id] = line.text;
          }
        });
        setTranscriptions(initialTrans);
      } else {
        // Perform segmentation
        await performSegmentation();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בטעינת שורות');
    } finally {
      setLoading(false);
    }
  };

  const performSegmentation = async () => {
    setLoading(true);
    setError('');

    try {
      const result = await segmentLines(documentId);
      setLines(result.lines);
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בסגמנטציה');
    } finally {
      setLoading(false);
    }
  };

  const handleTranscriptionChange = (lineId: number, text: string) => {
    setTranscriptions(prev => ({ ...prev, [lineId]: text }));
  };

  const handleSaveTranscriptions = async () => {
    setSaving(true);
    setError('');

    try {
      const transArray = Object.entries(transcriptions).map(([lineId, text]) => ({
        line_id: Number(lineId),
        text
      }));

      await transcribeLines(transArray);
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בשמירת תמלולים');
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="loading-center">
          <div className="loading"></div>
          <p>מבצע סגמנטציה של שורות...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>סגמנטציה ותמלול שורות</h2>
      <p>תמלל כל שורה שזוהתה בתמונה</p>

      {error && <div className="error">{error}</div>}

      {lines.length === 0 ? (
        <div className="empty-state">
          <p>לא נמצאו שורות. לחץ על "סגמנט מחדש" לניסיון נוסף.</p>
          <button className="button-primary" onClick={performSegmentation}>
            סגמנט מחדש
          </button>
        </div>
      ) : (
        <>
          <div className="stats">
            <div className="stat">
              <span className="stat-value">{lines.length}</span>
              <span className="stat-label">שורות</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {Object.keys(transcriptions).filter(id => transcriptions[Number(id)].trim()).length}
              </span>
              <span className="stat-label">מתומללות</span>
            </div>
          </div>

          <div className="lines-container">
            {lines.map(line => {
              const transcription = transcriptions[line.id] || '';

              return (
                <div key={line.id} className="line-item">
                  <div className="line-header">
                    <h4>שורה {line.line_order + 1}</h4>
                  </div>

                  <div className="line-content">
                    <div className="line-image">
                      <img src={line.image_url} alt={`Line ${line.line_order}`} />
                    </div>

                    <div className="line-transcription">
                      <textarea
                        value={transcription}
                        onChange={(e) => handleTranscriptionChange(line.id, e.target.value)}
                        placeholder="הקלד את תוכן השורה..."
                        rows={2}
                        className="transcription-input"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="action-buttons">
            <button className="button-secondary" onClick={onBack} disabled={saving}>
              חזור
            </button>
            <button
              className="button-primary"
              onClick={handleSaveTranscriptions}
              disabled={saving || Object.keys(transcriptions).length === 0}
            >
              {saving ? 'שומר...' : 'שמור תמלולים והמשך'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
