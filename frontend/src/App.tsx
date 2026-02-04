import { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import ImageEnhancement from './components/ImageEnhancement';
import CharacterSegmentation from './components/CharacterSegmentation';
import LineSegmentation from './components/LineSegmentation';
import ModelTraining from './components/ModelTraining';
import BatchProcessing from './components/BatchProcessing';
import './App.css';

type Step = 'upload' | 'enhance' | 'characters' | 'lines' | 'training' | 'batch';

function App() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');

  const handleUploadComplete = (docId: number, url: string) => {
    setDocumentId(docId);
    setImageUrl(url);
    setCurrentStep('enhance');
  };

  const handleEnhancementComplete = () => {
    setCurrentStep('characters');
  };

  const handleCharactersComplete = () => {
    setCurrentStep('lines');
  };

  const handleLinesComplete = () => {
    setCurrentStep('training');
  };

  const handleTrainingComplete = () => {
    setCurrentStep('batch');
  };

  const resetWorkflow = () => {
    setCurrentStep('upload');
    setDocumentId(null);
    setImageUrl('');
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'upload':
        return <ImageUpload onUploadComplete={handleUploadComplete} />;

      case 'enhance':
        return documentId ? (
          <ImageEnhancement
            documentId={documentId}
            originalImageUrl={imageUrl}
            onComplete={handleEnhancementComplete}
            onBack={() => setCurrentStep('upload')}
          />
        ) : null;

      case 'characters':
        return documentId ? (
          <CharacterSegmentation
            documentId={documentId}
            onComplete={handleCharactersComplete}
            onBack={() => setCurrentStep('enhance')}
          />
        ) : null;

      case 'lines':
        return documentId ? (
          <LineSegmentation
            documentId={documentId}
            onComplete={handleLinesComplete}
            onBack={() => setCurrentStep('characters')}
          />
        ) : null;

      case 'training':
        return (
          <ModelTraining
            onComplete={handleTrainingComplete}
            onBack={() => setCurrentStep('lines')}
          />
        );

      case 'batch':
        return (
          <BatchProcessing
            onBack={() => setCurrentStep('training')}
            onNewDocument={resetWorkflow}
          />
        );

      default:
        return null;
    }
  };

  const steps = [
    { key: 'upload', label: 'העלאה' },
    { key: 'enhance', label: 'שיפור תמונה' },
    { key: 'characters', label: 'סגמנטציה של תווים' },
    { key: 'lines', label: 'סגמנטציה של שורות' },
    { key: 'training', label: 'אימון מודל' },
    { key: 'batch', label: 'עיבוד מסמכים' }
  ];

  const currentStepIndex = steps.findIndex(s => s.key === currentStep);

  return (
    <div className="app">
      <header className="app-header">
        <h1>מערכת פענוח כתבי יד בעברית</h1>
        <p>מערכת לאימון ופענוח כתבי יד עם למידה מתמשכת</p>
      </header>

      <div className="container">
        {/* Progress indicator */}
        <div className="progress-bar">
          {steps.map((step, index) => (
            <div
              key={step.key}
              className={`progress-step ${index <= currentStepIndex ? 'active' : ''} ${
                index === currentStepIndex ? 'current' : ''
              }`}
              onClick={() => {
                // Allow navigation to previous steps only
                if (index < currentStepIndex && documentId) {
                  setCurrentStep(step.key as Step);
                }
              }}
              style={{ cursor: index < currentStepIndex ? 'pointer' : 'default' }}
            >
              <div className="step-number">{index + 1}</div>
              <div className="step-label">{step.label}</div>
            </div>
          ))}
        </div>

        {/* Current step content */}
        <div className="step-content">
          {renderStep()}
        </div>
      </div>
    </div>
  );
}

export default App;
