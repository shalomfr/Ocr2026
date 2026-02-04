import { useState, useEffect } from 'react';
import { segmentCharacters, getCharacters, labelGroup } from '../services/api';
import type { CharacterGroup } from '../types';
import './CharacterSegmentation.css';

interface CharacterSegmentationProps {
  documentId: number;
  onComplete: () => void;
  onBack: () => void;
}

export default function CharacterSegmentation({
  documentId,
  onComplete,
  onBack
}: CharacterSegmentationProps) {
  const [groups, setGroups] = useState<CharacterGroup>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [labels, setLabels] = useState<{ [groupId: string]: string }>({});

  useEffect(() => {
    loadCharacters();
  }, [documentId]);

  const loadCharacters = async () => {
    setLoading(true);
    setError('');

    try {
      // Try to load existing characters
      const existingGroups = await getCharacters(documentId);

      if (Object.keys(existingGroups).length > 0) {
        setGroups(existingGroups);
        // Initialize labels from existing data
        const initialLabels: { [groupId: string]: string } = {};
        Object.entries(existingGroups).forEach(([groupId, chars]) => {
          if (chars[0]?.label) {
            initialLabels[groupId] = chars[0].label;
          }
        });
        setLabels(initialLabels);
      } else {
        // Perform segmentation
        await performSegmentation();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בטעינת תווים');
    } finally {
      setLoading(false);
    }
  };

  const performSegmentation = async () => {
    setLoading(true);
    setError('');

    try {
      const result = await segmentCharacters(documentId, {
        clustering_method: 'kmeans'
      });

      setGroups(result.groups);
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בסגמנטציה');
    } finally {
      setLoading(false);
    }
  };

  const handleLabelChange = (groupId: string, label: string) => {
    setLabels(prev => ({ ...prev, [groupId]: label }));
  };

  const handleSaveLabels = async () => {
    setSaving(true);
    setError('');

    try {
      // Save all labels
      for (const [groupId, label] of Object.entries(labels)) {
        if (label.trim()) {
          await labelGroup(documentId, Number(groupId), label);
        }
      }

      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בשמירת תוויות');
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="loading-center">
          <div className="loading"></div>
          <p>מבצע סגמנטציה של תווים...</p>
        </div>
      </div>
    );
  }

  const groupIds = Object.keys(groups).filter(id => id !== '-1'); // Filter out noise

  return (
    <div className="card">
      <h2>סגמנטציה וקיבוץ תווים</h2>
      <p>תייג כל קבוצת תווים עם התו המתאים</p>

      {error && <div className="error">{error}</div>}

      {groupIds.length === 0 ? (
        <div className="empty-state">
          <p>לא נמצאו תווים. לחץ על "סגמנט מחדש" לניסיון נוסף.</p>
          <button className="button-primary" onClick={performSegmentation}>
            סגמנט מחדש
          </button>
        </div>
      ) : (
        <>
          <div className="stats">
            <div className="stat">
              <span className="stat-value">{groupIds.length}</span>
              <span className="stat-label">קבוצות</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {Object.values(groups).reduce((sum, chars) => sum + chars.length, 0)}
              </span>
              <span className="stat-label">תווים</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {Object.keys(labels).filter(id => labels[id].trim()).length}
              </span>
              <span className="stat-label">מתוייגים</span>
            </div>
          </div>

          <div className="groups-container">
            {groupIds.map(groupId => {
              const groupChars = groups[groupId];
              const label = labels[groupId] || '';

              return (
                <div key={groupId} className="character-group">
                  <div className="group-header">
                    <h4>קבוצה {groupId}</h4>
                    <span className="group-count">{groupChars.length} תווים</span>
                  </div>

                  <div className="group-label">
                    <input
                      type="text"
                      value={label}
                      onChange={(e) => handleLabelChange(groupId, e.target.value)}
                      placeholder="הקלד תו או מילה..."
                      maxLength={5}
                      className="label-input"
                    />
                  </div>

                  <div className="character-grid">
                    {groupChars.slice(0, 20).map(char => (
                      <div key={char.id} className="character-item">
                        <img src={char.image_url} alt={`Character ${char.id}`} />
                      </div>
                    ))}
                    {groupChars.length > 20 && (
                      <div className="character-item more">
                        +{groupChars.length - 20}
                      </div>
                    )}
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
              onClick={handleSaveLabels}
              disabled={saving || Object.keys(labels).length === 0}
            >
              {saving ? 'שומר...' : 'שמור תוויות והמשך'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
