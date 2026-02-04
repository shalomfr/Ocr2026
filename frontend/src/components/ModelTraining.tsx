import { useState, useEffect } from 'react';
import { startTraining, getTrainingStatus } from '../services/api';
import type { TrainingStatus } from '../types';
import './ModelTraining.css';

interface ModelTrainingProps {
  onComplete: () => void;
  onBack: () => void;
}

export default function ModelTraining({ onComplete, onBack }: ModelTrainingProps) {
  const [training, setTraining] = useState(false);
  const [status, setStatus] = useState<TrainingStatus>({
    is_training: false,
    current_epoch: 0,
    total_epochs: 0,
    loss: 0,
    accuracy: 0,
    num_samples: 0,
    progress: 0
  });
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    if (training) {
      interval = setInterval(async () => {
        try {
          const currentStatus = await getTrainingStatus();
          setStatus(currentStatus);

          if (!currentStatus.is_training && training) {
            setTraining(false);
            setSuccess(true);
          }
        } catch (err) {
          console.error('Error fetching status:', err);
        }
      }, 1000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [training]);

  const handleStartTraining = async () => {
    setTraining(true);
    setError('');
    setSuccess(false);

    try {
      await startTraining({
        epochs: 50,
        batch_size: 32,
        learning_rate: 0.001
      });
    } catch (err: any) {
      setError(err.response?.data?.error || 'שגיאה בהתחלת אימון');
      setTraining(false);
    }
  };

  return (
    <div className="card">
      <h2>אימון המודל</h2>
      <p>אמן את המודל על התווים המתוייגים</p>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">האימון הסתיים בהצלחה!</div>}

      {!training && !success ? (
        <div className="training-start">
          <div className="training-info">
            <h3>מידע על האימון</h3>
            <ul>
              <li>המודל ילמד לזהות תווים על בסיס התוויות שהזנת</li>
              <li>התהליך עשוי לקחת מספר דקות</li>
              <li>ניתן לצפות בהתקדמות בזמן אמת</li>
            </ul>
          </div>

          <button
            className="button-success"
            onClick={handleStartTraining}
            style={{ fontSize: '1.2rem', padding: '1rem 2rem' }}
          >
            התחל אימון
          </button>
        </div>
      ) : training ? (
        <div className="training-progress">
          <h3>מאמן מודל...</h3>

          <div className="progress-stats">
            <div className="stat">
              <span className="stat-label">דוגמאות אימון</span>
              <span className="stat-value">{status.num_samples}</span>
            </div>
            <div className="stat">
              <span className="stat-label">אפוק נוכחי</span>
              <span className="stat-value">
                {status.current_epoch} / {status.total_epochs}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">דיוק</span>
              <span className="stat-value">{(status.accuracy * 100).toFixed(2)}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Loss</span>
              <span className="stat-value">{status.loss.toFixed(4)}</span>
            </div>
          </div>

          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${status.progress}%` }} />
            <span className="progress-text">{status.progress}%</span>
          </div>

          <div className="training-animation">
            <div className="loading"></div>
            <p>מאמן... אנא המתן</p>
          </div>
        </div>
      ) : (
        <div className="training-complete">
          <svg
            width="80"
            height="80"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ color: '#28a745' }}
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>

          <h3>האימון הושלם בהצלחה!</h3>

          <div className="final-stats">
            <div className="stat">
              <span className="stat-label">דיוק סופי</span>
              <span className="stat-value">{(status.accuracy * 100).toFixed(2)}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">דוגמאות</span>
              <span className="stat-value">{status.num_samples}</span>
            </div>
          </div>

          <button className="button-primary" onClick={onComplete}>
            המשך לעיבוד מסמכים
          </button>
        </div>
      )}

      {!training && !success && (
        <div className="action-buttons">
          <button className="button-secondary" onClick={onBack}>
            חזור
          </button>
        </div>
      )}
    </div>
  );
}
