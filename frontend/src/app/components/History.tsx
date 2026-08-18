import { useState, useEffect } from "react";
import { Calendar, TrendingUp, Trash2, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";

interface HistoryItem {
  image: string;
  analysis: {
    disease: string;
    confidence: number;
    severity: string;
    solution: string[];
  };
  timestamp: string;
}

export function History() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

  useEffect(() => {
    const storedHistory = localStorage.getItem("agroguard_history");
    if (storedHistory) {
      setHistory(JSON.parse(storedHistory));
    }
  }, []);

  const handleDelete = (index: number) => {
    const newHistory = history.filter((_, i) => i !== index);
    setHistory(newHistory);
    localStorage.setItem("agroguard_history", JSON.stringify(newHistory));
    if (selectedItem === history[index]) {
      setSelectedItem(null);
    }
  };

  const handleClearAll = () => {
    if (confirm("Are you sure you want to clear all history?")) {
      setHistory([]);
      localStorage.removeItem("agroguard_history");
      setSelectedItem(null);
    }
  };

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <TrendingUp className="w-12 h-12 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">No Analysis History</h2>
        <p className="text-gray-600 max-w-sm">
          Your crop analysis history will appear here. Start by uploading a photo in the Chat tab.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-md mx-auto">
          <div>
            <h2 className="font-bold text-lg text-gray-800">Analysis History</h2>
            <p className="text-sm text-gray-600">{history.length} scans</p>
          </div>
          {history.length > 0 && (
            <Button
              onClick={handleClearAll}
              variant="outline"
              size="sm"
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              Clear All
            </Button>
          )}
        </div>
      </div>

      {/* History List */}
      <div className="p-4 space-y-3 max-w-md mx-auto pb-6">
        {history.map((item, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200"
          >
            <div
              onClick={() => setSelectedItem(selectedItem === item ? null : item)}
              className="cursor-pointer"
            >
              {/* Image and Basic Info */}
              <div className="flex gap-3 p-3">
                <img
                  src={item.image}
                  alt="Crop analysis"
                  className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {item.analysis.severity === "None" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-orange-600 flex-shrink-0" />
                    )}
                    <span className="font-semibold text-gray-800 truncate">
                      {item.analysis.disease}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
                    <Calendar className="w-3 h-3" />
                    <span>
                      {new Date(item.timestamp).toLocaleDateString()} at{" "}
                      {new Date(item.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                      {item.analysis.confidence}% confident
                    </span>
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${
                        item.analysis.severity === "None"
                          ? "bg-green-100 text-green-700"
                          : item.analysis.severity === "High"
                          ? "bg-red-100 text-red-700"
                          : "bg-orange-100 text-orange-700"
                      }`}
                    >
                      {item.analysis.severity}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(index);
                  }}
                  className="flex-shrink-0 p-2 hover:bg-red-50 rounded-lg transition-colors self-start"
                >
                  <Trash2 className="w-4 h-4 text-red-600" />
                </button>
              </div>

              {/* Expandable Details */}
              {selectedItem === item && (
                <div className="border-t border-gray-200 p-3 bg-gray-50 space-y-3">
                  <div>
                    <h4 className="font-semibold text-sm text-gray-800 mb-2">
                      Recommended Actions:
                    </h4>
                    <ul className="space-y-1.5">
                      {item.analysis.solution.map((step, idx) => (
                        <li key={idx} className="flex gap-2 text-sm text-gray-700">
                          <span className="text-green-600 font-bold flex-shrink-0">
                            {idx + 1}.
                          </span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
