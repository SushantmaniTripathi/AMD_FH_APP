# StayHeal — Intelligent Food Health-Style Ordering

StayHeal is a premium food-ordering interface featuring an intelligent health recommendation engine. It aligns a user's appetite with their physiological needs using real-time context (time, weather) and historical order data.

---

## 🚀 Local Setup

### 1. Backend (FastAPI)
- **Navigate to directory**: `cd backend`
- **Install dependencies**: `pip install -r requirements.txt`
- **Configure Environment**: 
  - Create a `.env` file based on `.env.example`.
  - Add your `WEATHER_API_KEY` (OpenWeatherMap).
  - Add your `GOOGLE_APPLICATION_CREDENTIALS` (Service Account JSON).
- **Run the server**: 
  ```bash
  uvicorn main:app --reload
  ```
  The API will be available at `http://localhost:8000`.

### 2. Frontend
- **Open the UI**: Simply open `frontend/index.html` in your web browser.
- **Port Matching**: Ensure the `API_BASE_URL` in `frontend/app.js` matches your backend address.

---

## 🛠 API Endpoint Reference

### `POST /recommend`
Rank menu items by health score and apply contextual modifiers.
- **Request**:
  ```json
  {
    "user_id": "user_123",
    "menu_items": [{"id": "1", "name": "Salad", "calories": 300, "protein": 20, "sugar": 5}],
    "context": {"hour": 12, "weather": "Clear"}
  }
  ```
- **Response**: Ranked items with `health_score`, `badge`, and `is_top_pick`.

### `POST /nudge`
Analyze order history and return a behavioral nudge message.
- **Request**:
  ```json
  { "user_history": [...] }
  ```

### `POST /summary`
Generate weekly textual insights from 7 days of data.

---

## ☁️ Deployment (GCP Cloud Run)

To deploy the backend to Cloud Run using the included `Dockerfile` and `cloudbuild.yaml`:

1.  **Submit Build**:
    ```bash
    gcloud builds submit --config cloudbuild.yaml \
      --substitutions=_WEATHER_API_KEY="your_key",_FIRESTORE_PROJECT_ID="your_pid"
    ```
2.  **Service Account**: Ensure the `stayheal-service-account` secret is stored in GCP Secret Manager as requested in the build config.

---

## 🧬 Scoring Logic

The `health_score` is calculated as follows:
- **Base**: `(100 - (calories / 10)) + (protein * 0.5) - (sugar * 0.8)`
- **Penalty**: `-10` for items ordered in the last 5 orders.
- **Contextual Modifiers**:
  - Late Night (21:00-05:00) + Heavy Food: `-20` points.
  - High Junk Ratio (>60%) + Healthy Item: `+15` points (positive reinforcement).
  - Raining + Comfort Food: `+5` points.

---

## 🎨 Design System
Built on "The Clinical Epicurean" design philosophy:
- **Primary Teal (#00685c)**: Trust and Health.
- **Secondary Orange (#984800)**: Appetite and Action.
- **Glassmorphism**: 20px backdrop blur for high-impact cards.
- **Typography**: Manrope for headlines, Inter for body text.
