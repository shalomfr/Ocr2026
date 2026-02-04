# תוכנית: מערכת פענוח כתבי יד בעברית (Hebrew OCR Training System)

## סקירה כללית
מערכת web-based לאימון ופענוח כתבי יד בעברית עם למידה מתמשכת. המערכת תאפשר העלאת תמונות, עיבוד ידני עם תצוגה אינטראקטיבית, אימון מודל ML, והרצה על מסמכים נוספים.

## ארכיטקטורה טכנית

### Stack טכנולוגי
- **Frontend**: React + TypeScript
- **Backend**: Python Flask + TensorFlow/Keras
- **עיבוד תמונה**: OpenCV + PIL
- **Database**: PostgreSQL (כי Render תומך בו טוב)
- **Storage**: Cloudinary או Render Disk לתמונות
- **Deployment**: Render (Web Service + PostgreSQL)

## מבנה הפרויקט

```
Ocr2026/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── requirements.txt       # Python dependencies
│   ├── config.py             # Configuration settings
│   ├── models/
│   │   ├── ocr_model.py      # TensorFlow/Keras OCR model
│   │   └── training.py       # Training logic
│   ├── services/
│   │   ├── image_processing.py    # Image enhancement & segmentation
│   │   ├── character_grouping.py  # Character clustering logic
│   │   └── line_segmentation.py   # Line detection
│   ├── routes/
│   │   ├── upload.py         # Image upload endpoints
│   │   ├── preprocessing.py   # Enhancement endpoints
│   │   ├── segmentation.py   # Segmentation endpoints
│   │   ├── labeling.py       # Character labeling endpoints
│   │   └── training.py       # Model training endpoints
│   └── database/
│       ├── db.py             # Database connection
│       └── models.py         # SQLAlchemy models
├── frontend/
│   ├── package.json
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ImageUpload.tsx
│   │   │   ├── ImageEnhancement.tsx      # Step 1: Enhancement UI
│   │   │   ├── CharacterSegmentation.tsx # Step 2: Character grouping
│   │   │   ├── LineSegmentation.tsx      # Step 3: Line transcription
│   │   │   ├── ModelTraining.tsx         # Step 4: Training UI
│   │   │   └── BatchProcessing.tsx       # Step 5: Run on pages
│   │   ├── services/
│   │   │   └── api.ts        # API calls
│   │   └── types/
│   │       └── index.ts      # TypeScript types
│   └── vite.config.ts
└── README.md
```

## תהליך העבודה (Workflow)

### שלב 1: העלאה ועיבוד ראשוני
**Frontend:**
- קומפוננטה להעלאת תמונה (drag & drop)
- הצגת תמונה מקורית

**Backend:**
- `POST /api/upload` - קבלת תמונה, שמירה ב-storage, החזרת ID
- שמירת metadata ב-DB (document_id, filename, upload_date)

### שלב 2: חידוד ושיפור תמונה (Interactive Enhancement)
**Frontend:**
- סליידרים לשליטה:
  - Brightness (בהירות)
  - Contrast (ניגודיות)
  - Sharpness (חדות)
  - Threshold (סף בינאריזציה)
  - Noise Reduction (הפחתת רעש)
- תצוגה real-time של התמונה המשופרת (עדכון כל 300ms עם debounce)
- כפתור "שמור והמשך"

**Backend:**
- `POST /api/enhance` - מקבל פרמטרים, מחזיר תמונה משופרת (base64 או URL)
- שימוש ב-OpenCV:
  - `cv2.convertScaleAbs()` לבהירות/ניגודיות
  - `cv2.GaussianBlur()` להפחתת רעש
  - `cv2.threshold()` לבינאריזציה
  - `cv2.filter2D()` לחידוד

### שלב 3: סגמנטציה של תווים וקיבוץ (Character Segmentation & Grouping)
**Frontend:**
- הצגת תמונה עם bounding boxes סביב כל תו מזוהה
- קיבוץ אוטומטי לפי דמיון ויזואלי (clustering)
- תצוגת גלריה: כל קבוצה בנפרד (grid של כל התווים הדומים)
- לכל קבוצה:
  - שדה טקסט להזנת התווית (תו בודד או מספר תווים, למשל "של")
  - כפתור X להסרת תווים שגויים מהקבוצה
  - גרירת תווים בין קבוצות
- כפתור "שמור תוויות"

**Backend:**
- `POST /api/segment/characters` - מבצע סגמנטציה של תווים:
  - Connected components analysis
  - שמירת coordinates של כל תו
  - קיבוץ אוטומטי באמצעות:
    - Feature extraction (HOG features)
    - K-means clustering או DBSCAN
  - החזרת מערך של קבוצות עם images
- `POST /api/label/characters` - שמירת תוויות שהוזנו:
  - character_id, label, group_id, document_id
  - שמירה ב-DB לאימון עתידי

**Database Schema:**
```sql
characters (
    id, document_id, image_path,
    bbox_x, bbox_y, bbox_w, bbox_h,
    label, group_id, is_valid
)
```

### שלב 4: סגמנטציה של שורות ותמלול (Line Segmentation & Transcription)
**Frontend:**
- הצגת תמונה עם קווים אופקיים המסמנים שורות
- לכל שורה:
  - תמונת השורה
  - שדה טקסט להקלדת התוכן המלא
  - כפתור עריכה/מחיקה
- כפתור "שמור תמלולים"

**Backend:**
- `POST /api/segment/lines` - סגמנטציה של שורות:
  - Horizontal projection profile
  - זיהוי רווחים בין שורות
  - חיתוך כל שורה
  - החזרת מערך של line images
- `POST /api/transcribe/lines` - שמירת תמלולים:
  - line_id, document_id, text, line_order
  - שמירה ב-DB

**Database Schema:**
```sql
lines (
    id, document_id, image_path,
    line_order, text, bbox_y_start, bbox_y_end
)
```

### שלב 5: אימון המודל (Model Training)
**Frontend:**
- לחיצה על "אמן מודל"
- מחוון progress bar עם:
  - מספר דוגמאות באימון
  - Epoch נוכחי
  - Loss & Accuracy
- הודעת סיום כשהאימון נגמר

**Backend:**
- `POST /api/train` - מתחיל אימון:
  - טעינת כל התוויות מ-DB
  - הכנת dataset (תמונות + labels)
  - Data augmentation (rotation, scaling, noise)
  - אימון CNN:
    - Architecture: Conv2D → MaxPool → Conv2D → MaxPool → Dense → Softmax
    - Input: תמונת תו 32x32 grayscale
    - Output: הסתברויות לכל תו (א-ת + רווח + ניקוד)
  - שמירת model weights
  - שימוש ב-Server-Sent Events (SSE) לעדכון progress
- `GET /api/train/status` - מצב האימון

**Model Architecture (TensorFlow/Keras):**
```python
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 1)),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(num_classes, activation='softmax')
])
```

### שלב 6: הרצה על עמודים נוספים (Batch Processing)
**Frontend:**
- העלאת מספר תמונות בבת אחת
- רשימת תמונות עם status (pending/processing/done)
- לחיצה על "הרץ OCR"
- הצגת תוצאות לכל עמוד:
  - תמונה מקורית
  - טקסט מפוענח
  - confidence score
  - אפשרות לתקן ולהוסיף לאימון

**Backend:**
- `POST /api/batch/upload` - העלאת מספר קבצים
- `POST /api/batch/process` - הרצת OCR על כולם:
  - עיבוד כל תמונה
  - סגמנטציה של שורות ותווים
  - חיזוי עם המודל המאומן
  - הרכבת טקסט מלא
  - שמירת תוצאות
- `GET /api/batch/results/:batch_id` - קבלת תוצאות

### שלב 7: למידה מתמשכת (Continuous Learning)
**Frontend:**
- בדף תוצאות, אפשרות ללחוץ "תקן ואמן"
- עריכת התוצאה
- הוספה לסט האימון
- אימון מחדש (incremental)

**Backend:**
- `POST /api/feedback` - קבלת תיקון מהמשתמש
- `POST /api/retrain` - אימון incremental:
  - טעינת model weights קיימים
  - אימון על דוגמאות חדשות בלבד
  - Fine-tuning עם learning rate נמוך

## Database Schema מלא

```sql
-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    original_image_path TEXT,
    enhanced_image_path TEXT,
    upload_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) -- 'uploaded', 'enhanced', 'segmented', 'labeled', 'trained', 'processed'
);

-- Characters table
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    image_path TEXT,
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_w INTEGER,
    bbox_h INTEGER,
    label VARCHAR(10), -- תו או מספר תווים
    group_id INTEGER,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lines table
CREATE TABLE lines (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    image_path TEXT,
    line_order INTEGER,
    text TEXT,
    bbox_y_start INTEGER,
    bbox_y_end INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Training history
CREATE TABLE training_runs (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    num_samples INTEGER,
    accuracy FLOAT,
    loss FLOAT,
    trained_at TIMESTAMP DEFAULT NOW()
);

-- Batch processing
CREATE TABLE batch_jobs (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50), -- 'pending', 'processing', 'completed', 'failed'
    total_pages INTEGER,
    processed_pages INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE batch_results (
    id SERIAL PRIMARY KEY,
    batch_job_id INTEGER REFERENCES batch_jobs(id),
    document_id INTEGER REFERENCES documents(id),
    extracted_text TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints סיכום

| Method | Endpoint | תיאור |
|--------|----------|-------|
| POST | /api/upload | העלאת תמונה בודדת |
| POST | /api/enhance | עיבוד ושיפור תמונה |
| POST | /api/segment/characters | סגמנטציה של תווים |
| POST | /api/segment/lines | סגמנטציה של שורות |
| POST | /api/label/characters | שמירת תוויות לתווים |
| POST | /api/transcribe/lines | שמירת תמלולי שורות |
| POST | /api/train | אימון המודל |
| GET | /api/train/status | סטטוס אימון |
| POST | /api/batch/upload | העלאת מספר תמונות |
| POST | /api/batch/process | הרצת OCR batch |
| GET | /api/batch/results/:id | קבלת תוצאות |
| POST | /api/feedback | תיקון ותגובה |
| POST | /api/retrain | אימון מחדש |

## תכונות נוספות חשובות

### 1. תמיכה ב-RTL
- Frontend עם direction: rtl לעברית
- תצוגה נכונה של טקסט מימין לשמאל

### 2. Character Features מתקדמים
- HOG (Histogram of Oriented Gradients) features
- תמיכה בניקוד (אופציונלי)
- זיהוי תווים מחוברים

### 3. Model Versioning
- שמירת גרסאות שונות של המודל
- אפשרות לחזור לגרסה קודמת
- השוואת ביצועים

### 4. Export/Import
- ייצוא dataset לשימוש חוזר
- ייצוא תוצאות OCR (TXT, JSON)
- ייבוא datasets מוכנים

## Deployment ל-Render

### Backend (Web Service)
```yaml
# render.yaml
services:
  - type: web
    name: hebrew-ocr-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DATABASE_URL
        fromDatabase:
          name: hebrew-ocr-db
          property: connectionString
```

### Frontend (Static Site)
```yaml
  - type: web
    name: hebrew-ocr-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: ./frontend/dist
```

### Database
- PostgreSQL instance בRender
- Backups אוטומטיים

### Storage
- אופציה 1: Render Disk (פשוט אבל לא persistent)
- אופציה 2: Cloudinary (מומלץ לתמונות)

## קבצים קריטיים לפיתוח

### Backend
1. `backend/app.py` - Flask app initialization
2. `backend/models/ocr_model.py` - TensorFlow model
3. `backend/services/image_processing.py` - OpenCV logic
4. `backend/services/character_grouping.py` - Clustering
5. `backend/requirements.txt`:
```
flask==3.0.0
flask-cors==4.0.0
tensorflow==2.15.0
opencv-python==4.8.1.78
pillow==10.1.0
numpy==1.24.3
scikit-learn==1.3.2
scikit-image==0.22.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
gunicorn==21.2.0
python-dotenv==1.0.0
```

### Frontend
1. `frontend/src/App.tsx` - Main app component
2. `frontend/src/components/ImageEnhancement.tsx` - שלב 2
3. `frontend/src/components/CharacterSegmentation.tsx` - שלב 3
4. `frontend/src/components/LineSegmentation.tsx` - שלב 4
5. `frontend/package.json`:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "react-router-dom": "^6.20.0",
    "react-dropzone": "^14.2.3",
    "react-draggable": "^4.4.6"
  }
}
```

## תהליך הפיתוח המומלץ

1. **Phase 1**: Backend infrastructure
   - Flask app + PostgreSQL
   - Upload & storage
   - Basic image processing

2. **Phase 2**: Image enhancement
   - OpenCV integration
   - Enhancement endpoint
   - React UI עם סליידרים

3. **Phase 3**: Character segmentation
   - Connected components
   - Clustering algorithm
   - Interactive labeling UI

4. **Phase 4**: Line segmentation
   - Horizontal projection
   - Line extraction
   - Transcription UI

5. **Phase 5**: ML Model
   - Dataset preparation
   - Model architecture
   - Training pipeline

6. **Phase 6**: Batch processing
   - OCR inference
   - Results display
   - Feedback loop

7. **Phase 7**: Deployment
   - Render configuration
   - Environment variables
   - Testing

## בדיקות (Verification)

### Backend Testing
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run tests
pytest backend/tests/

# Run development server
python backend/app.py
```

### Frontend Testing
```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Integration Testing
1. העלה תמונת דף כתב יד
2. שפר את התמונה עם הסליידרים
3. בדוק שהסגמנטציה עובדת
4. תייג מספר תווים
5. תמלל שורות
6. הרץ אימון
7. העלה דף נוסף והרץ OCR
8. בדוק תוצאות

## שיקולים נוספים

### ביצועים
- Lazy loading לתמונות
- Pagination לגלריית תווים
- Background jobs לאימון (Celery אופציונלי)
- Caching של תוצאות

### אבטחה
- File upload validation (רק תמונות)
- Rate limiting
- CORS configuration
- Environment variables לסודות

### UX
- Loading states
- Error handling
- הודעות הצלחה/כשלון
- Keyboard shortcuts (חץ ימין/שמאל לניווט בין קבוצות)
