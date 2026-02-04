# מערכת פענוח כתבי יד בעברית (Hebrew OCR Training System)

מערכת web-based מתקדמת לאימון ופענוח כתבי יד בעברית עם למידה מתמשכת.

## תכונות עיקריות

- 📤 העלאת תמונות כתבי יד
- 🎨 שיפור ועיבוד תמונה אינטראקטיבי
- ✂️ סגמנטציה אוטומטית של תווים ושורות
- 🏷️ תיוג תווים עם קיבוץ אוטומטי
- 🤖 אימון מודל ML (CNN) עם TensorFlow
- 📊 תצוגת התקדמות בזמן אמת
- 🔄 למידה מתמשכת והתאמת המודל

## Stack טכנולוגי

### Backend
- Python 3.11
- Flask (Web Framework)
- TensorFlow/Keras (Deep Learning)
- OpenCV (Image Processing)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- Cloudinary (Image Storage)

### Frontend
- React 18
- TypeScript
- Vite (Build Tool)
- Axios (HTTP Client)
- React Dropzone (File Upload)

## התקנה והפעלה

### דרישות מקדימות
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- (אופציונלי) Cloudinary account

### Backend Setup

1. התקן תלויות Python:
```bash
cd backend
pip install -r requirements.txt
```

2. צור קובץ `.env`:
```bash
cp .env.example .env
```

3. ערוך את `.env` עם ההגדרות שלך:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/hebrew_ocr
STORAGE_TYPE=cloudinary  # או 'local'
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

4. הרץ את השרת:
```bash
python app.py
```

השרת יעלה על `http://localhost:5000`

### Frontend Setup

1. התקן תלויות:
```bash
cd frontend
npm install
```

2. הרץ את שרת הפיתוח:
```bash
npm run dev
```

הממשק יעלה על `http://localhost:3000`

3. בניית production:
```bash
npm run build
```

## תהליך העבודה

### 1. העלאת תמונה
- גרור ושחרר תמונת דף כתב יד
- תמיכה בפורמטים: PNG, JPG, JPEG, TIF, TIFF, BMP

### 2. שיפור תמונה
- התאם פרמטרים:
  - בהירות (Brightness)
  - ניגודיות (Contrast)
  - הפחתת רעש (Blur)
  - חדות (Sharpen)
  - סף בינאריזציה (Threshold)
- תצוגה מקדימה בזמן אמת

### 3. סגמנטציה של תווים
- זיהוי אוטומטי של תווים בודדים
- קיבוץ תווים דומים באמצעות ML clustering
- תיוג קבוצות עם התווים המתאימים

### 4. סגמנטציה של שורות
- זיהוי אוטומטי של שורות טקסט
- תמלול ידני של כל שורה
- תצוגה לצד תמונת השורה

### 5. אימון המודל
- אימון CNN על התווים המתוייגים
- תצוגת התקדמות:
  - Epoch נוכחי
  - Loss & Accuracy
  - מספר דוגמאות
- שמירת המודל המאומן

### 6. עיבוד מסמכים נוספים
- העלאת מסמכים חדשים
- הרצת OCR אוטומטי
- תיקון ואימון מחדש

## ארכיטקטורת המודל

```python
Sequential([
    Conv2D(32, (3,3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D((2,2)),

    Conv2D(64, (3,3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D((2,2)),

    Conv2D(128, (3,3), activation='relu'),
    BatchNormalization(),
    MaxPooling2D((2,2)),

    Flatten(),
    Dense(256, activation='relu'),
    Dropout(0.5),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(num_classes, activation='softmax')
])
```

## API Endpoints

| Method | Endpoint | תיאור |
|--------|----------|-------|
| POST | `/api/upload` | העלאת תמונה בודדת |
| POST | `/api/enhance` | עיבוד ושיפור תמונה |
| POST | `/api/enhance/save` | שמירת תמונה משופרת |
| POST | `/api/segment/characters` | סגמנטציה של תווים |
| POST | `/api/segment/lines` | סגמנטציה של שורות |
| POST | `/api/label/characters` | שמירת תוויות לתווים |
| POST | `/api/label/group` | תיוג קבוצה שלמה |
| POST | `/api/transcribe/lines` | שמירת תמלולי שורות |
| POST | `/api/train` | אימון המודל |
| GET | `/api/train/status` | סטטוס אימון |
| GET | `/api/train/progress` | SSE stream להתקדמות |
| POST | `/api/retrain` | אימון מחדש incremental |
| GET | `/api/models` | רשימת מודלים מאומנים |
| POST | `/api/batch/upload` | העלאת מספר תמונות |
| GET | `/api/documents` | רשימת מסמכים |
| GET | `/api/characters/:id` | קבלת תווים למסמך |
| GET | `/api/lines/:id` | קבלת שורות למסמך |

## Deployment ל-Render

### Backend

1. צור Web Service חדש ב-Render
2. חבר את הrepository שלך
3. הגדר:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app`
4. הוסף PostgreSQL database
5. הגדר environment variables מ-`.env.example`

### Frontend

1. צור Static Site חדש ב-Render
2. הגדר:
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`
3. הגדר `VITE_API_URL` לכתובת הbackend

## Database Schema

### Documents
```sql
id, filename, original_image_path, enhanced_image_path,
upload_date, status
```

### Characters
```sql
id, document_id, image_path, bbox_x, bbox_y, bbox_w, bbox_h,
label, group_id, is_valid, created_at
```

### Lines
```sql
id, document_id, image_path, line_order, text,
bbox_y_start, bbox_y_end, created_at
```

### Training Runs
```sql
id, model_version, num_samples, accuracy, loss, trained_at
```

## אלפבית עברי נתמך

```
א ב ג ד ה ו ז ח ט י כ ך ל מ ם נ ן ס ע פ ף צ ץ ק ר ש ת
+ רווח, פיסוק בסיסי (. , ! ? - " ')
```

## Performance Optimization

- Lazy loading של תמונות
- Debounce על שינויי פרמטרים (300ms)
- Background jobs לאימון ארוך
- Caching של תוצאות עיבוד
- Batch processing למסמכים מרובים

## Security

- File upload validation
- CORS configuration
- Environment variables לסודות
- SQL injection protection (SQLAlchemy)
- Rate limiting (יש להוסיף)

## תרומה למערכת

1. Fork את הrepository
2. צור branch חדש (`git checkout -b feature/AmazingFeature`)
3. Commit השינויים (`git commit -m 'Add some AmazingFeature'`)
4. Push לbranch (`git push origin feature/AmazingFeature`)
5. פתח Pull Request

## רישיון

MIT License

## יוצר

מערכת זו נבנתה עבור פרויקט פענוח כתבי יד בעברית.

## תמיכה

לשאלות, בעיות או הצעות, פתח Issue ב-GitHub.
