# Quick Start Guide

## התקנה מהירה (5 דקות)

### דרישות
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### שלב 1: Clone והתקנה

```bash
# (אם יש git repo)
git clone <repo-url>
cd Ocr2026

# רוץ התקנה אוטומטית
chmod +x setup.sh
./setup.sh
```

### שלב 2: הגדרת Database

```bash
# צור database
createdb hebrew_ocr

# או דרך psql:
psql -U postgres
CREATE DATABASE hebrew_ocr;
\q
```

### שלב 3: הגדרת Backend

```bash
cd backend
cp .env.example .env

# ערוך .env עם:
# - DATABASE_URL (PostgreSQL connection string)
# - CLOUDINARY credentials (או שנה ל-STORAGE_TYPE=local)
```

### שלב 4: הרצה

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```
Backend: http://localhost:5000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend: http://localhost:3000

## שימוש מהיר

1. פתח http://localhost:3000
2. העלה תמונת כתב יד
3. שפר את התמונה עם הסליידרים
4. סגמנט תווים ותייג אותם
5. סגמנט שורות ותמלל אותן
6. אמן את המודל
7. עבד מסמכים נוספים!

## Troubleshooting

### Backend לא עולה
- בדוק שPostgreSQL רץ: `pg_isready`
- בדוק שהconnection string ב-.env נכון
- בדוק logs לשגיאות

### Frontend לא עולה
- מחק `node_modules` והתקן מחדש: `rm -rf node_modules && npm install`
- בדוק שהbackend רץ על port 5000

### תמונות לא נשמרות
- אם משתמש בCloudinary: בדוק את הcredentials
- אם משתמש ב-local storage: בדוק הרשאות על תיקיית uploads

## סביבת פיתוח

### Backend Development

```bash
cd backend
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .

# Lint
flake8
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Docker (אופציונלי)

אם אתה מעדיף להשתמש בDocker:

```bash
# Backend
cd backend
docker build -t hebrew-ocr-backend .
docker run -p 5000:5000 --env-file .env hebrew-ocr-backend

# Frontend
cd frontend
docker build -t hebrew-ocr-frontend .
docker run -p 3000:3000 hebrew-ocr-frontend
```

## Deploy ל-Render (1 קליק)

1. Fork את הrepository
2. צור account ב-Render.com
3. לחץ על "New" → "Blueprint"
4. בחר את הrepository
5. Render יזהה את `render.yaml` ויעלה הכל!

עדיין צריך להוסיף:
- Cloudinary credentials כEnvironment Variables
- Secret key

## עזרה נוספת

- README.md מלא: [README.md](./README.md)
- תיעוד API: [PLAN.md](./PLAN.md)
- Issues: פתח issue בGitHub
