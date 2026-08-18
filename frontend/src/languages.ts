// 23 Indian languages supported by AgroGuard AI
export interface Language {
  code: string;       // BCP-47 language code for Web Speech API
  whisperCode: string; // Whisper model language code
  name: string;       // English name
  nativeName: string; // Name in that language
  flag: string;       // Emoji flag/symbol
}

export const INDIAN_LANGUAGES: Language[] = [
  { code: "en", whisperCode: "en", name: "English", nativeName: "English", flag: "🇬🇧" },
  { code: "hi", whisperCode: "hi", name: "Hindi", nativeName: "हिंदी", flag: "🇮🇳" },
  { code: "ta", whisperCode: "ta", name: "Tamil", nativeName: "தமிழ்", flag: "🇮🇳" },
  { code: "te", whisperCode: "te", name: "Telugu", nativeName: "తెలుగు", flag: "🇮🇳" },
  { code: "kn", whisperCode: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ", flag: "🇮🇳" },
  { code: "ml", whisperCode: "ml", name: "Malayalam", nativeName: "മലയാളം", flag: "🇮🇳" },
  { code: "mr", whisperCode: "mr", name: "Marathi", nativeName: "मराठी", flag: "🇮🇳" },
  { code: "bn", whisperCode: "bn", name: "Bengali", nativeName: "বাংলা", flag: "🇮🇳" },
  { code: "gu", whisperCode: "gu", name: "Gujarati", nativeName: "ગુજરાતી", flag: "🇮🇳" },
  { code: "pa", whisperCode: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ", flag: "🇮🇳" },
  { code: "or", whisperCode: "or", name: "Odia", nativeName: "ଓଡ଼ିଆ", flag: "🇮🇳" },
  { code: "as", whisperCode: "as", name: "Assamese", nativeName: "অসমীয়া", flag: "🇮🇳" },
  { code: "mai", whisperCode: "hi", name: "Maithili", nativeName: "मैथिली", flag: "🇮🇳" },
  { code: "sat", whisperCode: "hi", name: "Santali", nativeName: "ᱥᱟᱱᱛᱟᱲᱤ", flag: "🇮🇳" },
  { code: "ks", whisperCode: "ur", name: "Kashmiri", nativeName: "کٲشُر", flag: "🇮🇳" },
  { code: "ne", whisperCode: "ne", name: "Nepali", nativeName: "नेपाली", flag: "🇮🇳" },
  { code: "sd", whisperCode: "sd", name: "Sindhi", nativeName: "سنڌي", flag: "🇮🇳" },
  { code: "kok", whisperCode: "hi", name: "Konkani", nativeName: "कोंकणी", flag: "🇮🇳" },
  { code: "mni", whisperCode: "hi", name: "Manipuri", nativeName: "মৈতৈলোন্", flag: "🇮🇳" },
  { code: "doi", whisperCode: "hi", name: "Dogri", nativeName: "डोगरी", flag: "🇮🇳" },
  { code: "bho", whisperCode: "hi", name: "Bhojpuri", nativeName: "भोजपुरी", flag: "🇮🇳" },
  { code: "ur", whisperCode: "ur", name: "Urdu", nativeName: "اردو", flag: "🇮🇳" },
  { code: "sa", whisperCode: "sa", name: "Sanskrit", nativeName: "संस्कृतम्", flag: "🇮🇳" },
];

export const DEFAULT_LANGUAGE = INDIAN_LANGUAGES[0]; // English

export const getLanguageByCode = (code: string): Language => {
  return INDIAN_LANGUAGES.find(l => l.code === code) || DEFAULT_LANGUAGE;
};