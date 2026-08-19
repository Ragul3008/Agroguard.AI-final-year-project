import { useState, useRef, useEffect, useCallback, memo } from "react";
import {
  Camera, Send, Loader2, CheckCircle2, AlertCircle,
  Mic, MicOff, Volume2, VolumeX, Globe, MapPin, ChevronDown,
  Navigation, Phone, X
} from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";
import logoImg from "../../assets/logo.png";
import {
  analyzeImage as analyzeImageAPI,
  sendChatMessage,
  whisperSpeechToText,
  textToSpeech,
  getNearbyHorticultureCenters,
  translateText
} from "../../api.ts";
import { INDIAN_LANGUAGES, DEFAULT_LANGUAGE, Language } from "../../languages";

// ─── Types ────────────────────────────────────────────────────────────────────

interface AdvisorySection {
  title: string;
  content: string;
  icon?: string;
}

interface AdvisoryResponse {
  summary: string;
  sections: AdvisorySection[];
  full_text: string;
}

interface AnalysisResult {
  disease: string;
  disease_display?: string;
  confidence: number;
  confidence_pct?: string;
  confidence_label?: "High" | "Medium" | "Low" | "Very Low";
  severity: string;
  advisory: AdvisoryResponse;  // Structured advisory response
  advisory_legacy?: string;    // Legacy full text for backward compatibility
  points: AnalysisPoint[];     // Kept for backward compatibility
  nearestCenter?: string;
}

interface AnalysisPoint {
  label: string;
  value: string;
}

interface Message {
  id: string;
  type: "user" | "ai";
  text?: string;
  image?: string;
  timestamp: Date;
  analysis?: AnalysisResult;
  translatedText?: string;     // holds translated version of text
  isTranslating?: boolean;
}

interface HorticultureCenter {
  name: string;
  address: string;
  phone?: string;
  distance?: string;
  latitude?: number;
  longitude?: number;
}

// ─── Utility: parse advisory paragraph into bullet points (legacy) ─────────────────────

function parseAdvisoryToPoints(advisory: string, disease: string, severity: string): AnalysisPoint[] {
  // Split on sentence boundaries, numbered items, or common delimiters
  const points: AnalysisPoint[] = [];

  // Always add disease + severity as first points
  points.push({ label: "🦠 Disease Detected", value: disease });
  points.push({ label: "⚠️ Severity Level", value: severity });

  if (!advisory) return points;

  // Try to split into sentences/steps
  const raw = advisory
    .replace(/\d+\.\s*/g, "|||") // numbered lists
    .replace(/•\s*/g, "|||")      // bullet chars
    .replace(/\n/g, "|||")        // newlines
    .split("|||")
    .map(s => s.trim())
    .filter(s => s.length > 10);

  if (raw.length <= 1) {
    // Single paragraph — split on ". " boundaries
    const sentences = advisory.match(/[^.!?]+[.!?]+/g) || [advisory];
    const actionLabels = [
      "💊 Immediate Action",
      "🌿 Treatment Step",
      "🛡️ Prevention",
      "📋 Follow-up",
      "📞 Seek Help",
    ];
    sentences.slice(0, 5).forEach((s, i) => {
      points.push({ label: actionLabels[i] || `📌 Step ${i + 1}`, value: s.trim() });
    });
  } else {
    const actionLabels = [
      "💊 Immediate Action",
      "🌿 Treatment",
      "🛡️ Prevention",
      "📋 Follow-up",
      "📞 Advisory",
      "🔍 Monitor",
    ];
    raw.slice(0, 6).forEach((s, i) => {
      points.push({ label: actionLabels[i] || `📌 Step ${i + 1}`, value: s });
    });
  }

  return points;
}

// ─── Language Selector Component ─────────────────────────────────────────────

const LanguageSelector = memo(function LanguageSelector({
  selected,
  onChange
}: {
  selected: Language;
  onChange: (lang: Language) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-green-300 rounded-full text-sm font-medium text-green-700 hover:bg-green-50 shadow-sm transition-all"
      >
        <Globe className="w-4 h-4" />
        <span>{selected.nativeName}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 max-h-72 overflow-y-auto">
          <div className="p-2">
            <p className="text-xs text-gray-400 px-2 py-1 font-medium uppercase tracking-wide">
              Select Language
            </p>
            {INDIAN_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => { onChange(lang); setOpen(false); }}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-left hover:bg-green-50 transition-colors ${
                  selected.code === lang.code ? "bg-green-100 text-green-800 font-semibold" : "text-gray-700"
                }`}
              >
                <span className="text-base">{lang.flag}</span>
                <div>
                  <p className="text-sm font-medium">{lang.nativeName}</p>
                  <p className="text-xs text-gray-400">{lang.name}</p>
                </div>
                {selected.code === lang.code && (
                  <CheckCircle2 className="w-4 h-4 text-green-600 ml-auto" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

// ─── Text cleaning helper for Speech ──────────────────────────────────────────

function cleanTextForSpeech(text: string): string {
  if (!text) return "";
  return text
    .replace(/https?:\/\/\S+|www\.\S+/g, "")
    .replace(/[\*\_\~\`\#\|]/g, "")
    .replace(/^\s*[\-\*\•\>]+\s*/gm, "")
    .replace(/\n\s*[\-\*\•\>]+\s*/g, " ")
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E6}-\u{1F1FF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B00}-\u{2BFF}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}]/gu, "")
    .replace(/\s*[:\-]\s*/g, ", ")
    .replace(/\s+/g, " ")
    .trim();
}

const BCP47_LANG_MAP: Record<string, string> = {
  ta: "ta-IN",
  hi: "hi-IN",
  te: "te-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  mr: "mr-IN",
  gu: "gu-IN",
  pa: "pa-IN",
  bn: "bn-IN",
  en: "en-IN",
};

// ─── Audio Player Button ──────────────────────────────────────────────────────

const AudioButton = memo(function AudioButton({
  text,
  language
}: {
  text: string;
  language: Language;
}) {
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlay = async () => {
    // If already playing — stop
    if (playing) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      window.speechSynthesis?.cancel();
      setPlaying(false);
      return;
    }

    const cleanedText = cleanTextForSpeech(text);
    if (!cleanedText) return;

    try {
      setLoading(true);

      // Try high-quality backend gTTS first
      try {
        const audioUrl = await textToSpeech(cleanedText, language.code);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onended = () => setPlaying(false);
        audio.onerror = () => {
          // fallback to browser TTS
          speakWithBrowser(cleanedText, language.code);
        };
        await audio.play();
        setPlaying(true);
      } catch {
        // Fallback: browser Web Speech API
        speakWithBrowser(cleanedText, language.code);
      }
    } catch {
      toast.error("Could not play audio. Please try again.");
      setPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  const speakWithBrowser = (rawText: string, langCode: string) => {
    if (!window.speechSynthesis) {
      toast.error("Audio not supported in this browser.");
      return;
    }
    window.speechSynthesis.cancel();

    const cleanedText = cleanTextForSpeech(rawText);
    const utter = new SpeechSynthesisUtterance(cleanedText);
    const bcp47 = BCP47_LANG_MAP[langCode.toLowerCase()] || langCode;
    utter.lang = bcp47;
    utter.rate = 0.9;

    // Try to find a matching native voice
    const voices = window.speechSynthesis.getVoices();
    const match = voices.find(
      v => v.lang.toLowerCase() === bcp47.toLowerCase() ||
           v.lang.toLowerCase().startsWith(langCode.toLowerCase())
    );
    if (match) utter.voice = match;

    utter.onstart = () => setPlaying(true);
    utter.onend = () => setPlaying(false);
    utter.onerror = () => setPlaying(false);
    window.speechSynthesis.speak(utter);
  };

  useEffect(() => {
    return () => {
      if (audioRef.current) audioRef.current.pause();
      window.speechSynthesis?.cancel();
    };
  }, []);

  return (
    <button
      onClick={handlePlay}
      disabled={loading}
      title={playing ? "Stop audio" : `Listen in ${language.nativeName}`}
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all border ${
        playing
          ? "bg-orange-100 border-orange-400 text-orange-700 hover:bg-orange-200"
          : "bg-green-50 border-green-300 text-green-700 hover:bg-green-100"
      }`}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : playing ? (
        <VolumeX className="w-3.5 h-3.5" />
      ) : (
        <Volume2 className="w-3.5 h-3.5" />
      )}
      {playing ? "Stop" : "Listen"}
    </button>
  );
});

// ─── Horticulture Centers Modal ───────────────────────────────────────────────

const HorticultureMap = memo(function HorticultureMap({
  onClose
}: {
  onClose: () => void;
}) {
  const [centers, setCenters] = useState<HorticultureCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const parseCenters = (data: any): HorticultureCenter[] => {
      console.log("getNearbyHorticultureCenters response:", data);
      if (Array.isArray(data)) return data;
      if (data && Array.isArray(data.centers)) return data.centers;
      if (data && Array.isArray(data.centres)) return data.centres;
      return [];
    };

    const fetchCenters = async () => {
      try {
        setLoading(true);

        // Try to get GPS location first for accurate results
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (pos) => {
              const data = await getNearbyHorticultureCenters(
                pos.coords.latitude,
                pos.coords.longitude
              );
              setCenters(parseCenters(data));
              setLoading(false);
            },
            async (err) => {
              console.warn("GPS error in modal, calling without coords:", err);
              toast.warning("Please turn on Location Services (GPS) for accurate results!");
              // GPS denied/timeout — fallback without params
              const data = await getNearbyHorticultureCenters();
              setCenters(parseCenters(data));
              setLoading(false);
            },
            { timeout: 5000, maximumAge: 60000 }
          );
        } else {
          // No GPS — use fallback
          toast.warning("Location Services are not supported on your browser.");
          const data = await getNearbyHorticultureCenters();
          setCenters(parseCenters(data));
          setLoading(false);
        }
      } catch (err) {
        console.error("Failed to load nearby centers:", err);
        setError("Could not load nearby centers. Please check your connection.");
        setLoading(false);
      }
    };

    fetchCenters();
  }, []);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h3 className="font-bold text-gray-800 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-green-600" />
              Nearby Horticulture Centers
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-8 h-8 text-green-600 animate-spin" />
              <p className="text-sm text-gray-500">Finding centers near you...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 rounded-xl p-4 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {!loading && !error && centers.length === 0 && (
            <div className="text-center py-12">
              <MapPin className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No centers found nearby.</p>
              <p className="text-gray-400 text-xs mt-1">
                Try contacting your district agriculture office.
              </p>
            </div>
          )}

          {!loading && centers.map((center, idx) => (
            <div
              key={idx}
              className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 text-sm">{center.name}</h4>
                  <p className="text-xs text-gray-500 mt-1 flex items-start gap-1">
                    <MapPin className="w-3 h-3 mt-0.5 flex-shrink-0 text-green-500" />
                    {center.address}
                  </p>
                  {center.phone && (
                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                      <Phone className="w-3 h-3 text-green-500" />
                      {center.phone}
                    </p>
                  )}
                </div>
                {center.distance && (
                  <span className="text-xs bg-green-600 text-white px-2 py-1 rounded-full font-medium flex-shrink-0">
                    {center.distance}
                  </span>
                )}
              </div>

              {center.latitude && center.longitude && (
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${center.latitude},${center.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 flex items-center justify-center gap-1.5 w-full py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  Get Directions
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

// ─── Formatted Markdown Text Component ───────────────────────────────────────

const FormattedMessage = memo(function FormattedMessage({ text }: { text: string }) {
  if (!text) return null;

  const lines = text.split("\n");

  return (
    <div className="flex flex-col space-y-1">
      {lines.map((line, lineIdx) => {
        // Convert markdown bullet points to actual bullet character
        let processedLine = line;
        if (processedLine.trim().startsWith("* ")) {
          processedLine = processedLine.replace(/^\s*\*\s*/, "• ");
        } else if (processedLine.trim().startsWith("- ")) {
          processedLine = processedLine.replace(/^\s*-\s*/, "• ");
        }

        const parts = processedLine.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);

        return (
          <span key={lineIdx} className={processedLine.trim() === "" ? "h-2 block" : ""}>
            {parts.map((part, partIdx) => {
              if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
                return (
                  <strong key={partIdx} className="font-bold text-green-900">
                    {part.slice(2, -2)}
                  </strong>
                );
              }
              if (
                part.startsWith("*") &&
                part.endsWith("*") &&
                part.length >= 2 &&
                !part.startsWith("**")
              ) {
                return (
                  <strong key={partIdx} className="font-bold text-green-900">
                    {part.slice(1, -1)}
                  </strong>
                );
              }
              if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
                return (
                  <code key={partIdx} className="bg-black/10 px-1 py-0.5 rounded text-xs font-mono">
                    {part.slice(1, -1)}
                  </code>
                );
              }
              return part;
            })}
            {lineIdx < lines.length - 1 && <br />}
          </span>
        );
      })}
    </div>
  );
});

// ─── Analysis Card Component ──────────────────────────────────────────────────

const AnalysisCard = memo(function AnalysisCard({
  analysis,
  language
}: {
  analysis: AnalysisResult;
  language: Language;
}) {
  // Use structured advisory if available, fallback to legacy
  const advisory = analysis.advisory;
  const fullText = advisory?.full_text || analysis.advisory_legacy || analysis.points.map(p => `${p.label}: ${p.value}`).join(". ");
  const displayDisease = analysis.disease_display || analysis.disease;

  // Confidence label color
  const confidenceLabel = analysis.confidence_label || "Medium";
  const confidenceColor = confidenceLabel === "High" ? "bg-green-100 text-green-800" :
                          confidenceLabel === "Medium" ? "bg-yellow-100 text-yellow-800" :
                          confidenceLabel === "Low" ? "bg-orange-100 text-orange-800" :
                          "bg-red-100 text-red-800";

  // Severity color
  const severityLower = analysis.severity?.toLowerCase();
  const isHealthy = severityLower === "none" || severityLower === "healthy";
  const severityColor = isHealthy ? "bg-green-100 text-green-800" :
                        severityLower === "high" ? "bg-red-100 text-red-800" :
                        severityLower === "medium" ? "bg-orange-100 text-orange-800" :
                        "bg-yellow-100 text-yellow-800";

  return (
    <div className="mt-3 border-t border-gray-100 pt-3 space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isHealthy ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0" />
          )}
          <span className="font-bold text-gray-800 text-sm">{analysis.disease_display || analysis.disease}</span>
        </div>
        {/* Listen button for full advisory */}
        <AudioButton text={advisory?.full_text || fullText} language={language} />
      </div>

      {/* Summary */}
      {advisory?.summary && (
        <p className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">{advisory.summary}</p>
      )}

      {/* Confidence + Severity chips */}
      <div className="flex gap-2 flex-wrap">
        <span className={`${confidenceColor} text-xs font-semibold px-2.5 py-1 rounded-full`}>
          {analysis.confidence_label || "Medium"} ({analysis.confidence}%)
        </span>
        <span className={`${severityColor} text-xs font-semibold px-2.5 py-1 rounded-full`}>
          {analysis.severity} severity
        </span>
      </div>

      {/* Advisory Sections */}
      {advisory?.sections && advisory.sections.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
            Recommended Actions
          </p>
          <div className="space-y-2">
            {advisory.sections.map((section, idx) => (
              <div
                key={idx}
                className="flex gap-2.5 bg-white rounded-lg p-3 border border-gray-100 shadow-sm"
              >
                <span className="text-base flex-shrink-0">{section.icon || "📋"}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-700">{section.title}</p>
                  <p className="text-xs text-gray-600 mt-0.5 leading-relaxed whitespace-pre-wrap">{section.content}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legacy bullet points fallback */}
      {!advisory?.sections?.length && analysis.points && analysis.points.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
            Recommended Actions
          </p>
          <div className="space-y-2">
            {analysis.points
              .filter(p => p.label !== "🦠 Disease Detected" && p.label !== "⚠️ Severity Level")
              .map((point, idx) => (
                <div
                  key={idx}
                  className="flex gap-2.5 bg-white rounded-lg p-2.5 border border-gray-100 shadow-sm"
                >
                  <span className="text-sm flex-shrink-0">{point.label.split(" ")[0]}</span>
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-gray-700">
                      {point.label.split(" ").slice(1).join(" ")}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{point.value}</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Low confidence warning */}
      {analysis.confidence_label === "Low" || analysis.confidence_label === "Very Low" ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-yellow-800">Low Confidence Detection</p>
              <p className="text-xs text-yellow-700 mt-1">
                The model is not very confident in this result. Consider retaking the photo with better lighting
                or consulting a local agricultural expert for confirmation.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Nearest center */}
      {analysis.nearestCenter && (
        <div className="bg-blue-50 rounded-lg p-2.5 border border-blue-100">
          <p className="text-xs font-semibold text-blue-700 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            Nearest Help Center
          </p>
          <p className="text-xs text-blue-600 mt-0.5">{analysis.nearestCenter}</p>
        </div>
      )}
    </div>
  );
});

// ─── Thumbnail helper (compress base64 image to ~200px for localStorage) ──────

function compressToThumbnail(dataUrl: string, maxSize = 200): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);
      const canvas = document.createElement("canvas");
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      canvas.getContext("2d")?.drawImage(img, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL("image/jpeg", 0.6));
    };
    img.onerror = () => resolve(dataUrl); // fallback: use original
    img.src = dataUrl;
  });
}

// ─── Main Chat Component ──────────────────────────────────────────────────────

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "ai",
      text: "👋 Hello! I'm AgroGuard AI — your personal banana farming advisor. I can help you with:\n\n🖼️ **Upload a photo** for instant disease detection & treatment advice\n💬 **Ask questions** about diseases, fertilizers, irrigation, pests, and cultivation\n🌍 **Multi-language support** — respond in 22 Indian languages\n📍 **Find nearby centers** — locate horticulture clinics for expert help\n\nWhat can I help you with today?",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loadingType, setLoadingType] = useState<"image" | "text">("image");
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false); // Whisper recording state
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(DEFAULT_LANGUAGE);
  const [showMap, setShowMap] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const browserRecognitionRef = useRef<any>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Whisper Voice Input ────────────────────────────────────────────────────

  const startWhisperRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        stream.getTracks().forEach(t => t.stop());

        try {
          setIsAnalyzing(true);
          const result = await whisperSpeechToText(audioBlob, selectedLanguage.whisperCode);
          if (result.transcript) {
            setInputText(prev => prev + (prev ? " " : "") + result.transcript);
            toast.success(`🎤 Transcribed in ${selectedLanguage.nativeName}`);
          } else {
            toast.error("Could not transcribe. Please try again.");
          }
        } catch {
          // Fallback to browser speech recognition
          toast.info("Using browser speech recognition as fallback...");
          startBrowserRecognition();
        } finally {
          setIsAnalyzing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.success(`🎙️ Recording... Tap mic again to stop`, { duration: 3000 });
    } catch (err) {
      toast.error("Microphone access denied. Please allow microphone permission.");
      // Fallback to browser speech recognition
      startBrowserRecognition();
    }
  }, [selectedLanguage]);

  const stopWhisperRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  // ── Browser Speech Recognition (fallback) ─────────────────────────────────

  const startBrowserRecognition = useCallback(() => {
    const SpeechRecognition =
      (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;

    if (!SpeechRecognition) {
      toast.error("Speech recognition not supported. Please use Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    browserRecognitionRef.current = recognition;
    recognition.lang = selectedLanguage.code;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputText(prev => prev + (prev ? " " : "") + transcript);
      setIsListening(false);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognition.start();
    setIsListening(true);
  }, [selectedLanguage]);

  const toggleVoiceInput = useCallback(() => {
    if (isRecording) {
      stopWhisperRecording();
    } else if (isListening) {
      browserRecognitionRef.current?.stop();
      setIsListening(false);
    } else {
      startWhisperRecording();
    }
  }, [isRecording, isListening, startWhisperRecording, stopWhisperRecording]);

  // ── Image Analysis ─────────────────────────────────────────────────────────

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file only!");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Image too large! Please upload under 10MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = async (event) => {
      const imageUrl = event.target?.result as string;
      setSelectedImage(imageUrl);
    };
    reader.readAsDataURL(file);
    
    e.target.value = '';
  };

  // ── Text Message ───────────────────────────────────────────────────────────

  const handleSendMessage = async () => {
    if (!inputText.trim() && !selectedImage) return;

    if (selectedImage) {
      const text = inputText || "Please analyze this banana plant image";
      const imageUrl = selectedImage;
      
      const userMessage: Message = {
        id: Date.now().toString(),
        type: "user",
        image: imageUrl,
        text: text,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      setInputText("");
      setSelectedImage(null);
      setLoadingType("image");
      setIsAnalyzing(true);

      try {
        const data = await analyzeImageAPI(imageUrl, selectedLanguage.code);
        
        const advisoryResponse = data.advisory as any;
        const confidenceLabel = data.confidence_label || "Medium";

        const analysis: AnalysisResult = {
          disease: data.disease || "Unknown",
          disease_display: data.disease_display,
          confidence: Math.round((data.confidence || 0) * 100),
          confidence_pct: data.confidence_pct,
          confidence_label: confidenceLabel,
          severity: data.severity || "Unknown",
          advisory: advisoryResponse,
          advisory_legacy: data.advisory || data.solution || "",
          points: [], 
          nearestCenter: data.nearest_center,
        };

        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          text: `Analysis complete for ${selectedLanguage.nativeName}! Detected: ${analysis.disease}`,
          analysis,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiMessage]);

        const thumbnail = await compressToThumbnail(imageUrl);
        const history = JSON.parse(localStorage.getItem("agroguard_history") || "[]");
        history.unshift({ image: thumbnail, analysis, timestamp: new Date().toISOString() });
        localStorage.setItem("agroguard_history", JSON.stringify(history.slice(0, 50)));

      } catch (err) {
        console.error("Analysis error:", err);
        const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
        toast.error(`Analysis failed: ${errorMsg}`);
        const errMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          text: `Sorry, I could not analyze this image. Error: ${errorMsg}`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errMessage]);
      } finally {
        setIsAnalyzing(false);
      }
    } else {
      const userMessage: Message = {
        id: Date.now().toString(),
        type: "user",
        text: inputText,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      const question = inputText;
      setInputText("");
      setLoadingType("text");
      setIsAnalyzing(true);

      try {
        const reply = await sendChatMessage(question, selectedLanguage.code);
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          text: reply,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiMessage]);
      } catch {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "ai",
          text: "Sorry, I couldn't process your question. Please try again!",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiMessage]);
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  // ── Language Change ────────────────────────────────────────────────────────

  const handleLanguageChange = useCallback((lang: Language) => {
    setSelectedLanguage(lang);
    toast.success(`Language set to ${lang.nativeName}`, { duration: 2000 });
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-green-50 to-emerald-50">

      {/* ── Top Bar ── */}
      <div className="bg-white border-b border-gray-100 px-4 py-2.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <img
            src={logoImg}
            alt="AgroGuard AI"
            className="w-9 h-9 rounded-full object-cover shadow-sm bg-white p-0.5"
          />
          <div>
            <p className="text-sm font-semibold text-gray-800">AgroGuard AI</p>
            <p className="text-xs text-green-600">Banana Disease Detection</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Map / Nearby Centers button */}
          <button
            onClick={() => setShowMap(true)}
            title="Find nearby horticulture centers"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full text-xs font-medium text-green-700 hover:bg-green-100 transition-all"
          >
            <MapPin className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Centers</span>
          </button>

          {/* Language selector */}
          <LanguageSelector selected={selectedLanguage} onChange={handleLanguageChange} />
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[88%] rounded-2xl p-4 ${
                message.type === "user"
                  ? "bg-green-600 text-white rounded-br-sm"
                  : "bg-white shadow-md rounded-bl-sm"
              }`}
            >
              {message.image && (
                <img
                  src={message.image}
                  alt="Uploaded crop"
                  className="rounded-xl mb-2 w-full object-cover max-h-48"
                />
              )}

              {/* Text with listen button for AI messages */}
              {message.text && (
                <div className="flex items-start justify-between gap-2">
                  <div className="text-sm leading-relaxed flex-1">
                    <FormattedMessage text={message.text} />
                  </div>
                  {message.type === "ai" && !message.analysis && (
                    <AudioButton text={message.text} language={selectedLanguage} />
                  )}
                </div>
              )}

              {/* Analysis card with bullet points */}
              {message.analysis && (
                <AnalysisCard analysis={message.analysis} language={selectedLanguage} />
              )}

              <p className={`text-xs mt-2 ${message.type === "user" ? "text-green-200" : "text-gray-400"}`}>
                {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>
        ))}

        {/* Analyzing indicator */}
        {isAnalyzing && (
          <div className="flex justify-start">
            <div className="bg-white shadow-md rounded-2xl rounded-bl-sm p-4 flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-green-600 animate-spin" />
              <span className="text-sm text-gray-600">
                {isRecording ? "Transcribing your voice..." : loadingType === "text" ? "🤔 Analyzing your question..." : "🔍 Analyzing your crop image..."}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Input Bar ── */}
      <div className="bg-white border-t border-gray-100 p-4 shadow-lg">
        <div className="max-w-md mx-auto space-y-3">

          {/* Recording indicator */}
          {isRecording && (
            <div className="flex items-center gap-2 bg-red-50 rounded-xl px-3 py-2 border border-red-200">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs text-red-600 font-medium">
                Recording... Tap mic to stop and transcribe with Whisper AI
              </span>
            </div>
          )}

          {/* Selected Image Preview */}
          {selectedImage && (
            <div className="relative inline-block w-20 h-20 mb-1">
              <img src={selectedImage} alt="Selected" className="w-full h-full object-cover rounded-lg border-2 border-green-200" />
              <button 
                onClick={() => setSelectedImage(null)}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 shadow-sm"
                title="Remove image"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Text + Voice row */}
          <div className="flex gap-2">
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Ask me about diseases, fertilizers, pests... or upload a photo in ${selectedLanguage.nativeName}`}
              className="flex-1 resize-none min-h-[44px] max-h-[100px] text-sm"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />

            {/* Whisper mic button */}
            <Button
              onClick={toggleVoiceInput}
              variant="outline"
              title={
                isRecording
                  ? "Stop recording (Whisper AI will transcribe)"
                  : `Record voice in ${selectedLanguage.nativeName}`
              }
              className={`h-[44px] px-3 transition-all ${
                isRecording
                  ? "bg-red-100 border-red-500 text-red-600 hover:bg-red-200 animate-pulse"
                  : isListening
                  ? "bg-orange-100 border-orange-400 text-orange-600"
                  : "border-green-400 text-green-600 hover:bg-green-50"
              }`}
            >
              {isRecording || isListening ? (
                <MicOff className="w-5 h-5" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </Button>

            {/* Send button */}
            <Button
              onClick={handleSendMessage}
              disabled={(!inputText.trim() && !selectedImage) || isAnalyzing}
              className="bg-green-600 hover:bg-green-700 h-[44px] px-3"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>

          {/* Upload photo button */}
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            className="w-full border-green-400 text-green-700 hover:bg-green-50 font-medium"
          >
            <Camera className="w-4 h-4 mr-2" />
            Upload Crop Photo for Analysis
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp,image/heic,image/heif"
            capture="environment"
            onChange={handleImageUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* ── Nearby Centers Modal ── */}
      {showMap && <HorticultureMap onClose={() => setShowMap(false)} />}
    </div>
  );
}