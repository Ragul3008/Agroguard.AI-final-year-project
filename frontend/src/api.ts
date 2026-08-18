// API base URL from environment variable, with local fallback
// API base URL from environment variable, with local fallback
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// ─── REGISTER ────────────────────────────────────
export const register = async (
  name: string,
  phone: string,
  email: string,
  password: string,
  village: string,
  district: string,
  state: string
) => {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, phone, email, password, village, district, state })
  });
  return response.json();
};

// ─── LOGIN ───────────────────────────────────────
export const login = async (emailOrPhone: string, password: string) => {
  const trimmed = emailOrPhone.trim();
  const isPhone = /^\+?\d{10,15}$/.test(trimmed);
  const endpoint = isPhone ? `${BASE_URL}/auth/login` : `${BASE_URL}/auth/login/email`;
  const payload = isPhone
    ? { phone: trimmed, password }
    : { email: trimmed, password };

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return response.json();
};

// ─── GOOGLE LOGIN ────────────────────────────────
export const googleLogin = async (idToken: string) => {
  const response = await fetch(`${BASE_URL}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken })
  });
  return response.json();
};

// ─── FORGOT PASSWORD ─────────────────────────────
export const forgotPassword = async (email: string) => {
  const response = await fetch(`${BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  return response.json();
};

// ─── RESET PASSWORD ──────────────────────────────
export const resetPassword = async (email: string, otp: string, newPassword: string) => {
  const response = await fetch(`${BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp, new_password: newPassword })
  });
  return response.json();
};

// ─── PROFILE ─────────────────────────────────────
export const getMyProfile = async () => {
  const token = localStorage.getItem("agroguard_token");
  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!response.ok) throw new Error("Failed to fetch profile");
  return response.json();
};

export const updateProfile = async (data: { name?: string, village?: string, district?: string, state?: string }) => {
  const token = localStorage.getItem("agroguard_token");
  const response = await fetch(`${BASE_URL}/auth/me`, {
    method: "PUT",
    headers: { 
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}` 
    },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error("Failed to update profile");
  return response.json();
};

// ─── ANALYZE IMAGE ───────────────────────────────
export const analyzeImage = async (imageBase64: string, language: string = "en") => {
  const token = localStorage.getItem("agroguard_token");
  if (!token) {
    throw new Error("Authentication token not found. Please login first.");
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25000); // 25s timeout

  try {
    // Convert data URL to blob
    const response = await fetch(imageBase64);
    if (!response.ok) {
      throw new Error(`Failed to convert image data: ${response.statusText}`);
    }
    const blob = await response.blob();

    // Create FormData with required fields
    const formData = new FormData();
    formData.append("image", blob, "image.jpg");
    formData.append("language", language);
    
    // Optionally add location if available from navigator
    if (navigator.geolocation) {
      try {
        const position = await new Promise<GeolocationCoordinates>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(
            pos => resolve(pos.coords),
            err => reject(err),
            { timeout: 5000, maximumAge: 300000 }
          );
        });
        formData.append("latitude", position.latitude.toString());
        formData.append("longitude", position.longitude.toString());
      } catch {
        // Location not available, continue without it
        console.debug("Location not available, continuing without coordinates");
      }
    }

    const predictResponse = await fetch(`${BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!predictResponse.ok) {
      const errorData = await predictResponse.text();
      console.error(`Backend returned ${predictResponse.status}:`, errorData);
      throw new Error(`Server error: ${predictResponse.status} - ${errorData}`);
    }
    
    const result = await predictResponse.json();
    return result;
  } catch (error) {
    clearTimeout(timeoutId);
    console.error("Analysis Error:", error);
    throw error;
  }
};

// ─── TRANSLATE TEXT ───────────────────────────────
// Called when user selects a language AFTER analysis
export const translateText = async (text: string, targetLanguage: string) => {
  const token = localStorage.getItem("agroguard_token");
  const response = await fetch(`${BASE_URL}/translate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ text, target_language: targetLanguage })
  });
  return response.json();
};

// ─── WHISPER SPEECH TO TEXT ───────────────────────
// Uses backend Whisper model for accurate transcription
export const whisperSpeechToText = async (audioBlob: Blob, language: string = "en") => {
  const token = localStorage.getItem("agroguard_token");
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language", language);

  const response = await fetch(`${BASE_URL}/speech/transcribe`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`
    },
    body: formData
  });
  return response.json();
  // Expected: { transcript: "...", detected_language: "..." }
};

// ─── TEXT TO SPEECH ───────────────────────────────
// Backend converts text to audio in selected language
export const textToSpeech = async (text: string, language: string = "en") => {
  const token = localStorage.getItem("agroguard_token");
  const response = await fetch(`${BASE_URL}/speech/synthesize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ text, language })
  });
  // Returns audio blob
  const audioBlob = await response.blob();
  return URL.createObjectURL(audioBlob);
};

// ─── NEARBY HORTICULTURE CENTERS ─────────────────
// Always gets the device GPS first, then calls Geoapify via backend
export const getNearbyHorticultureCenters = async (latitude?: number, longitude?: number) => {
  const token = localStorage.getItem("agroguard_token");

  const params = new URLSearchParams();
  if (latitude !== undefined && latitude !== null)  params.append("latitude",  latitude.toString());
  if (longitude !== undefined && longitude !== null) params.append("longitude", longitude.toString());

  const response = await fetch(`${BASE_URL}/maps/nearby-centers?${params.toString()}`, {
    method: "GET",
    headers: { "Authorization": `Bearer ${token}` }
  });
  return response.json();
};

// ─── SEND CHAT MESSAGE ────────────────────────────
export const sendChatMessage = async (message: string, language: string = "en"): Promise<string> => {
  const token = localStorage.getItem("agroguard_token");
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

  try {
    // Use FormData format to match backend endpoint
    const formData = new FormData();
    formData.append("message", message);
    formData.append("language", language);

    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    if (response.ok) {
      const data = await response.json();
      return data.reply || data.response || data.message || "I couldn't generate a response. Please try again.";
    } else {
      console.error(`Chat endpoint returned ${response.status}`);
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (e) {
    clearTimeout(timeoutId);
    console.error("Chat backend error:", e);
    // fallback to local responses if backend chat not available
  }

  // Local fallback responses
  const msg = message.toLowerCase();
  if (msg.includes("bbtv") || msg.includes("bunchy")) {
    return "🦠 **BBTV (Banana Bunchy Top Virus)**: No cure exists. Immediate action: Uproot infected plants completely and burn them. Control aphid vectors with Imidacloprid spray every 7-14 days. Always use certified disease-free TC (tissue culture) planting material for new plantings.";
  } else if (msg.includes("sigatoka") || msg.includes("leaf spot")) {
    return "🍃 **Sigatoka Diseases** (Black or Yellow): Remove heavily infected leaves. Apply fungicides (Propiconazole 0.1% or Mancozeb 0.2%) every 10-14 days depending on season. Improve field ventilation by reducing excess suckers. Maintain proper drainage. Ensure drip irrigation — avoid overhead watering.";
  } else if (msg.includes("panama") || msg.includes("wilt")) {
    return "🌱 **Panama Disease (Fusarium Wilt)**: No chemical cure. Uproot all infected plants immediately and burn them. Quarantine the field. Use soil solarization (cover with polythene for 6-8 weeks). Replant ONLY with resistant varieties (Grand Nain, FHIA-01) using certified disease-free TC suckers.";
  } else if (msg.includes("fertilizer") || msg.includes("nutrients")) {
    return "🌿 **Banana Fertilizer Schedule**: Apply NPK @ 200:60:300 g per plant per year in 4 split doses. Year-round: Include organic mulch @ 5-10 kg per plant, add micronutrients (Zn, Fe, Mn, B) @ 50g per plant twice yearly, apply lime if pH is below 6.0.";
  } else if (msg.includes("water") || msg.includes("irrigation")) {
    return "💧 **Irrigation Guide**: Banana needs 25-50mm water per week depending on season. Drip irrigation is ideal — maintains soil moisture at 70-75% and prevents foliar diseases. Avoid waterlogging which promotes Panama disease and root rot.";
  } else if (msg.includes("weevil") || msg.includes("pest")) {
    return "🐛 **Pseudostem Weevil Control**: Install pheromone traps @ 10 per hectare. Apply Carbofuran 3G @ 40g per plant at pseudostem base. Use Beauveria bassiana (biological control). Remove old pseudostems within 5 days of harvest.";
  } else if (msg.includes("hello") || msg.includes("hi") || msg.includes("hey")) {
    return "👋 Hello! I'm AgroGuard AI, your friendly banana farming advisor. I can help you with:\n• 🖼️ Upload plant photos for disease diagnosis\n• 💊 Treatment recommendations for detected diseases\n• 🌱 Fertilizer and soil management guidance\n• 💧 Irrigation and pest control advice\n• 📚 General banana cultivation tips\n\nWhat would you like to know about banana farming?";
  } else {
    return "I'm AgroGuard AI, specialized in banana farming and disease management. Ask me about:\n• 🦠 Specific diseases (Panama, Sigatoka, BBTV, Weevil, Anthracnose)\n• 💊 Treatment methods and spraying schedules\n• 🌱 Fertilizers, soil health, and compost\n• 💧 Irrigation and water management\n• 🐛 Pest control and prevention tips\n\nOr upload a plant photo for instant disease detection!";
  }
};