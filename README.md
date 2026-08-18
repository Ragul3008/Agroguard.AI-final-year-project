# AgroGuard AI: Intelligent Banana Crop Disease Detection & Generative Advisory System

> **Annamalai University — Department of Computer Science & Engineering (Artificial Intelligence & Machine Learning)**  
> **B.E. CSE (AI & ML) Final Year Project**

---

## 📋 Project Information

*   **Project Name:** AgroGuard AI
*   **Domain:** Computer Vision, Natural Language Processing, Generative AI, Smart Agriculture
*   **Academic Year:** 2023 - 2024 / 2024 - 2025
*   **Team Members:**
    *   **Kabilan R K**
    *   **Ragul J**
    *   **Sanjai J**
    *   **Karthikeyan S**
*   **Project Guide:** **Dr. G. Arulselvi** (Department of CSE, Annamalai University)

---

## 📖 Abstract & Problem Statement

Banana is one of the most critical agricultural produce globally, supporting the livelihoods of millions of farmers. However, banana crops are highly susceptible to severe diseases, including:
1.  **Panama Wilt** (*Fusarium oxysporum*)
2.  **Black Sigatoka**
3.  **Yellow Sigatoka**
4.  **Pseudostem Weevil**
5.  **Banana Bunchy Top Virus (BBTV)**
6.  **Anthracnose**

Early detection and immediate advisory are paramount to preventing extensive yield loss. Traditional diagnosis methods are slow, subjective, and require in-person agricultural experts. 

**AgroGuard AI** is a complete, scalable, and responsive full-stack platform designed to empower farmers with immediate diagnosis and actionable regional-language treatment advisories. By leveraging **PyTorch ConvNeXt Small Deep Learning models** for disease classification, **Google Gemini 2.5 Flash** for dynamic advisory generation (aligned with **ICAR-NRCB Trichy guidelines**), **OpenAI Whisper** for multilingual speech-to-text input, and **Google Maps API** for nearest horticulture assistance, AgroGuard AI bridges the diagnostic gap.

---

## ⚡ Key Features

*   📸 **AI Crop Disease Diagnosis:** High-accuracy classification of 6 major banana diseases and healthy crop identification using a customized deep learning pipeline.
*   🗣️ **Voice-Enabled Multilingual Support:** High accessibility for farmers via speech-to-text (Whisper) in multiple Indian languages: **Tamil, Hindi, Malayalam, Telugu, Kannada, and English**.
*   🤖 **Generative Treatment Advisory:** Dynamic guidelines generated in the farmer's selected language using Gemini 2.5 Flash, strictly referenced to ICAR-NRCB (National Research Centre for Banana) protocols.
*   🗺️ **Geospatial Horticulture Locator:** Integrates with the Google Maps API to guide farmers to the nearest government agricultural help/extension center.
*   📊 **Analytics Dashboard & Scan History:** Fast, localized history storage and interactive visualization of crop diagnostic statistics using Recharts.
*   🔐 **Secure JWT-Based Authentication:** Role-based farmer login and encrypted user session tokens for tracking historical records safely.

---

## 🏗️ System Architecture

The following sequence diagram outlines the operational workflow of AgroGuard AI when a farmer uploads an image or requests advice:

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as Farmer (Web/Mobile App UI)
    participant Front as React Frontend SPA
    participant Back as FastAPI Backend Service
    database DB as PostgreSQL Database
    participant DL as ResNet50 Classifier
    participant Gemini as Google Gemini AI (LLM)
    participant Maps as Google Maps API

    Farmer->>Front: Select Language & Upload Plant Photo
    Front->>Front: Downscale & Compress Image to Thumbnail (History store)
    Front->>Back: POST /api/v1/predict (Image, Location, Language)
    activate Back
    Note over Back: Preprocesses image to tensor
    Back->>DL: Feed Tensor to Model
    DL-->>Back: Return Disease Name & Confidence
    
    rect rgb(240, 248, 255)
        Note over Back, Gemini: Generative advisory layer
        Back->>Gemini: Request Treatment Plan (ICAR-NRCB context in selected language)
        Gemini-->>Back: Return Native-Language Treatment Guide
    end

    rect rgb(255, 245, 230)
        Note over Back, Maps: Geospatial analysis
        Back->>Maps: Query nearest center (coordinates/IP location)
        Maps-->>Back: Return nearest Horticulture Center details
    end

    Back->>DB: Save prediction log & associate with Farmer ID
    DB-->>Back: Transaction Confirmed
    Back-->>Front: Return Prediction JSON (Disease, Advisory, Center details)
    deactivate Back
    Front->>Front: Save to local history + render graphs
    Front-->>Farmer: Show disease classification, severity, treatment guide, and Google Map location
```

---

## 💻 Technology Stack

### Frontend Architecture
*   **Core Library:** React 18 (TypeScript)
*   **Build Tool:** Vite 6
*   **Styling & Design System:** TailwindCSS v4, Radix UI Primitives, Lucide React (Icons), Framer Motion / Motion v12 (Micro-animations)
*   **Routing & State:** React Router v7, React Contexts
*   **Data Visualization:** Recharts (Dynamic agricultural statistics)

### Backend API Architecture
*   **Framework:** FastAPI (Python 3.12, fully asynchronous)
*   **Execution Server:** Uvicorn
*   **Database ORM:** SQLAlchemy (Async) with asyncpg driver
*   **Rate Limiting:** SlowAPI (Token bucket per IP)
*   **Security:** JWT Authentication (via python-jose and bcrypt)

### AI, Machine Learning, & Integrations
*   **Computer Vision Classifier:** PyTorch (custom fine-tuned ConvNeXt Small Architecture)
*   **Generative AI Service:** Google GenAI SDK (Gemini 2.5 Flash model)
*   **Speech-to-Text Model:** OpenAI Whisper (Medium/Base model integration)
*   **Geospatial Maps:** Google Maps API (Direction & Center Location)

---

## 🗄️ Database Schema & ORM Models

AgroGuard AI relies on two primary database tables managed asynchronously:

### 1. `farmers` Table
Stores registered farmers, credentials, and geographic regions.
*   `id` (Integer, Primary Key): Unique Identifier.
*   `name` (String): Full name of the farmer.
*   `phone` (String, Unique Index): Core authentication token & username.
*   `email` (String, Unique Index): Optional registration contact.
*   `password_hash` (String): Secure hashed passwords using bcrypt.
*   `village`, `district`, `state`: Regional tracking parameters.

### 2. `predictions` Table
Logs scans and detailed diagnostic history.
*   `id` (Integer, Primary Key): Unique scan identifier.
*   `farmer_id` (Integer, Foreign Key): Links to `farmers.id`.
*   `disease` (String): Classified disease/Healthy state.
*   `confidence` (Float) & `confidence_pct` (String): Machine learning model certainty metrics.
*   `severity` (String): Estimated damage scale.
*   `advisory` (Text): Full localized Gemini treatment guide text.
*   `latitude` & `longitude` (Float): Physical location coordinates of the crop.
*   `nearest_center` (String): Closest ICAR extension center address.
*   `model_version` (String): Running classification model version.
*   `created_at` (DateTime): Automated timestamping of the analysis.

---

## 🚀 Installation & Local Development Setup

Follow these instructions to run the entire stack locally.

### Prerequisites
*   Python 3.12+ installed.
*   Node.js (v18+) and npm/pnpm/yarn installed.
*   PostgreSQL running locally or hosted on the cloud.

### 1. Backend Setup
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    # Windows activation:
    .\venv\Scripts\activate
    # macOS/Linux activation:
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements_utf8.txt
    ```
4.  Configure Environment Variables:
    *   Create a `.env` file from the sample config:
        ```bash
        cp .env.example .env
        ```
    *   Configure your keys and databases in `.env`:
        ```env
        DATABASE_URL=postgresql+asyncpg://<username>:<password>@localhost:5432/<database_name>
        MODEL_PATH=saved_models/agroguard_banana_convnext_v3.pth
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY
        SECRET_KEY=YOUR_JWT_SECRET_KEY
        ```
5.  Launch the FastAPI server:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   Interactive API Docs will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2.  Install packages:
    ```bash
    npm install
    ```
3.  Run the Vite development server:
    ```bash
    npm run dev
    ```
    *   The user interface will run at [http://localhost:5173](http://localhost:5173)

---

## 🔧 Recent Performance & Quality Optimizations

To ensure production-grade reliability and lightning-fast loading speeds on low-bandwidth rural networks, the following changes were successfully implemented:

1.  **LocalStorage Memory Footprint Reduction:**
    *   *Problem:* Storing large raw Base64 images (~5MB) was causing the local storage to freeze on the History page.
    *   *Solution:* Integrated HTML5 Canvas image downscaling directly in `Chat.tsx` to compress uploaded photos into a tiny `200px` thumbnail (~10KB) prior to disk insertion, reducing loading time from several seconds to instantaneous.
2.  **Keystroke Latency Elimination (Typing Lag):**
    *   *Problem:* Re-renders on each keystroke in the agricultural search/chat inputs were triggering redundant renders of the maps and charts.
    *   *Solution:* Memoized heavy components (`AudioButton`, `AnalysisCard`, `HorticultureMap`) using `React.memo` and wrapped main triggers inside `useCallback` to prevent unnecessary component updates.
3.  **Vite Bundler Code-Splitting & Lazy Loading:**
    *   *Problem:* Heavy analytical components (Recharts, Maps) were causing a massive initial JS download penalty.
    *   *Solution:* Integrated dynamic imports (`React.lazy`) and React `<Suspense>` loaders into routes. Custom Vite chunks splits the libraries (Recharts, Material-UI, Radix) into smaller, on-demand payloads.
4.  **Backend Translation Correctness & Dynamic Multilingual Routing:**
    *   *Problem:* LLM output ignored Tamil/Hindi selection due to English-only prompt constraints.
    *   *Solution:* Refactored backend prompts in `advisory_service.py` to compile translation rules dynamically, and plumbed API language form keys straight to Gemini prompt templates to guarantee responses in native languages.
5.  **Graceful Network Interruption Timeouts:**
    *   *Problem:* Network rate-limiting stalls would leave the UI frozen on "Analyzing...".
    *   *Solution:* Integrated `AbortController` timeouts globally. Standard chat requests abort after 15 seconds, and model predictions expire after 25 seconds, reporting elegant alerts back to the farmer.
