import { useState, useEffect, useCallback } from 'react';
import { enhanceImage, saveEnhancedImage } from '../services/api';
import type { EnhancementParams } from '../types';
import './ImageEnhancement.css';

interface ImageEnhancementProps {
  documentId: number;
  originalImageUrl: string;
  onComplete: () => void;
  onBack: () => void;
}

export default function ImageEnhancement({
  documentId,
  originalImageUrl,
  onComplete,
  onBack
}: ImageEnhancementProps) {
  const [params, setParams] = useState<EnhancementParams>({
    brightness: 0,
    contrast: 1.0,
    blur: 0,
    threshold: null,
    sharpen: 0
  });

  const [enhancedImage, setEnhancedImage] = useState<string>(originalImageUrl);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  const updateEnhancement = useCallback(async (newParams: EnhancementParams) => {
    setLoading(true);
    setError('');

    try {
      const result = await enhanceImage(documentId, newParams);
      setEnhancedImage(result.image);
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בעיבוד התמונה');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const handleParamChange = (key: keyof EnhancementParams, value: number | null) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);

    // Debounce the enhancement call
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    const timer = setTimeout(() => {
      updateEnhancement(newParams);
    }, 300);

    setDebounceTimer(timer);
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');

    try {
      await saveEnhancedImage(documentId, params);
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בשמירת התמונה');
      setSaving(false);
    }
  };

  const handleReset = () => {
    const defaultParams: EnhancementParams = {
      brightness: 0,
      contrast: 1.0,
      blur: 0,
      threshold: null,
      sharpen: 0
    };
    setParams(defaultParams);
    updateEnhancement(defaultParams);
  };

  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [debounceTimer]);

  return (
    <div className="card">
      <h2>שיפור ועיבוד תמונה</h2>
      <p>התאם את הפרמטרים לשיפור איכות התמונה</p>

      {error && <div className="error">{error}</div>}

      <div className="enhancement-container">
        <div className="image-preview">
          <h3>תמונה משופרת</h3>
          <div className="image-wrapper">
            {loading && (
              <div className="loading-overlay">
                <div className="loading"></div>
              </div>
            )}
            <img src={enhancedImage} alt="Enhanced" />
          </div>
        </div>

        <div className="controls">
          <h3>פרמטרים</h3>

          <div className="control-group">
            <label>
              <span>בהירות: {params.brightness}</span>
              <input
                type="range"
                min="-100"
                max="100"
                value={params.brightness}
                onChange={(e) => handleParamChange('brightness', Number(e.target.value))}
              />
            </label>
          </div>

          <div className="control-group">
            <label>
              <span>ניגודיות: {params.contrast.toFixed(2)}</span>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.1"
                value={params.contrast}
                onChange={(e) => handleParamChange('contrast', Number(e.target.value))}
              />
            </label>
          </div>

          <div className="control-group">
            <label>
              <span>הפחתת רעש: {params.blur}</span>
              <input
                type="range"
                min="0"
                max="15"
                step="2"
                value={params.blur}
                onChange={(e) => handleParamChange('blur', Number(e.target.value))}
              />
            </label>
          </div>

          <div className="control-group">
            <label>
              <span>חדות: {params.sharpen}</span>
              <input
                type="range"
                min="0"
                max="10"
                value={params.sharpen}
                onChange={(e) => handleParamChange('sharpen', Number(e.target.value))}
              />
            </label>
          </div>

          <div className="control-group">
            <label>
              <span>סף בינאריזציה: {params.threshold ?? 'כבוי'}</span>
              <input
                type="range"
                min="0"
                max="255"
                value={params.threshold ?? 127}
                onChange={(e) => handleParamChange('threshold', Number(e.target.value))}
              />
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={params.threshold !== null}
                  onChange={(e) => handleParamChange('threshold', e.target.checked ? 127 : null)}
                />
                <span>הפעל</span>
              </label>
            </label>
          </div>

          <div className="button-group">
            <button
              className="button-secondary"
              onClick={handleReset}
              disabled={loading || saving}
            >
              איפוס
            </button>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button className="button-secondary" onClick={onBack} disabled={saving}>
          חזור
        </button>
        <button
          className="button-primary"
          onClick={handleSave}
          disabled={loading || saving}
        >
          {saving ? 'שומר...' : 'שמור והמשך'}
        </button>
      </div>
    </div>
  );
}
