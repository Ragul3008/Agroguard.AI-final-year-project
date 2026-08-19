import { Sprout, Target, Zap, Shield, Users, Lightbulb, Github, Linkedin, Instagram, Heart } from "lucide-react";
import { useState, useEffect } from "react";
import logoImg from "../../assets/logo.png";
import ragulImg from "../../assets/ragul.jpg";
import kabilanImg from "../../assets/kabilan.jpeg";

const teamMembers = [
  {
    name: "Sanjai J",
    image: "https://github.com/sxnjai23.png",
    github: "https://github.com/sxnjai23",
    linkedin: "https://linkedin.com/in/sanjai",
    instagram: "https://instagram.com/sxnjii_23",
  },
  {
    name: "Karthikeyan S",
    image: "https://github.com/karthikeyan9042.png",
    github: "https://github.com/karthikeyan9042",
    linkedin: "https://www.linkedin.com/in/karthikeyans9042/",
    instagram: "https://www.instagram.com/call_me___sk____?igsh=MXFrcDBub3R4cXltZQ==",
  },
  {
    name: "Ragul J",
    image: ragulImg,
    github: "https://github.com/Ragul3008",
    linkedin: "https://www.linkedin.com/in/ragul-jayakumar/",
    instagram: "https://www.instagram.com/rxgul.cpp?igsh=MW5ybXJxYXJvOHh4eA==",
  },
  {
    name: "Kabilan RK",
    image: kabilanImg,
    github: "https://github.com/kabilan-ML-Dev",
    linkedin: "https://www.linkedin.com/in/ml-kabilan-r-k/",
    instagram: "https://www.instagram.com/kabilan_r_k?igsh=MWJrZ2lqczlldDJsNw==",
  },
];

export function About() {
  const [shuffled, setShuffled] = useState(teamMembers);

  useEffect(() => {
    setShuffled([...teamMembers].sort(() => Math.random() - 0.5));
  }, []);

  const features = [
    {
      icon: Zap,
      title: "AI-Powered Analysis",
      description: "Advanced machine learning algorithms analyze your crop images in seconds",
    },
    {
      icon: Shield,
      title: "Disease Detection",
      description: "Identify various crop diseases with high accuracy and confidence levels",
    },
    {
      icon: Lightbulb,
      title: "Smart Solutions",
      description: "Get personalized treatment recommendations based on disease severity",
    },
    {
      icon: Users,
      title: "Easy to Use",
      description: "Simply upload a photo and receive instant analysis and guidance",
    },
  ];

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="max-w-md mx-auto p-6 space-y-6 pb-8">
        {/* Header */}
        <div className="text-center">
          <img
            src={logoImg}
            alt="AgroGuard AI Logo"
            className="w-24 h-24 rounded-2xl object-cover shadow-lg mx-auto mb-4 bg-white p-1"
          />
          <h1 className="text-3xl font-bold text-green-800 mb-2">AgroGuard.ai</h1>
          <p className="text-gray-600 leading-relaxed">
            Your AI-Powered Crop Health Assistant
          </p>
        </div>

        {/* Mission */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-800">Our Mission</h2>
          </div>
          <p className="text-gray-700 leading-relaxed">
            AgroGuard.ai empowers farmers and agricultural enthusiasts with cutting-edge
            artificial intelligence technology to protect their crops. Our mission is to make
            advanced crop disease detection accessible to everyone, helping to ensure food
            security and sustainable agriculture worldwide.
          </p>
        </div>

        {/* Features */}
        <div className="space-y-3">
          <h2 className="text-xl font-bold text-gray-800">Key Features</h2>
          <div className="grid gap-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="bg-white rounded-xl shadow-md p-4 flex gap-4 hover:shadow-lg transition-shadow"
                >
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Icon className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-1">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">How It Works</h2>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                1
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-1">Capture</h3>
                <p className="text-sm text-gray-600">
                  Take a clear photo of your crop showing any concerning symptoms
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                2
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-1">Analyze</h3>
                <p className="text-sm text-gray-600">
                  Our AI analyzes the image and identifies potential diseases
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                3
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 mb-1">Treat</h3>
                <p className="text-sm text-gray-600">
                  Follow our personalized recommendations to protect your crops
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-xl shadow-md p-4 text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">95%+</div>
            <p className="text-xs text-gray-600">Accuracy Rate</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-4 text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">50+</div>
            <p className="text-xs text-gray-600">Diseases Detected</p>
          </div>
          <div className="bg-white rounded-xl shadow-md p-4 text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">24/7</div>
            <p className="text-xs text-gray-600">Available</p>
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-3 flex items-center gap-2">
            <Heart className="w-5 h-5 text-red-500" />
            Meet the Developers
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4 text-sm">
            We are a dedicated team of AI/ML developers, building AgroGuard to empower farmers globally.
          </p>
          <div className="space-y-4">
            {shuffled.map((member, index) => (
              <div key={index} className="flex items-center gap-4 p-3 border border-gray-100 rounded-xl bg-gray-50/50">
                <img
                  src={member.image}
                  alt={member.name}
                  className="w-14 h-14 rounded-full object-cover border-2 border-green-500"
                />
                <div className="flex-1">
                  <h3 className="font-bold text-gray-800">{member.name}</h3>
                  <div className="flex gap-3 mt-2">
                    <a href={member.github} target="_blank" rel="noopener noreferrer"
                      className="text-gray-600 hover:text-black">
                      <Github className="w-4 h-4" />
                    </a>
                    <a href={member.linkedin} target="_blank" rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800">
                      <Linkedin className="w-4 h-4" />
                    </a>
                    <a href={member.instagram} target="_blank" rel="noopener noreferrer"
                      className="text-pink-500 hover:text-pink-700">
                      <Instagram className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Note */}
        <div className="bg-green-100 rounded-xl p-4 border border-green-200">
          <p className="text-sm text-green-800 text-center leading-relaxed">
            💚 Protecting crops, ensuring food security, and supporting sustainable
            agriculture through AI innovation.
          </p>
        </div>
      </div>
    </div>
  );
}
