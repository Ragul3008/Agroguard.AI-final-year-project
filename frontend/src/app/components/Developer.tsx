import { Github, Linkedin, Mail, Globe, Code, Heart, Instagram } from "lucide-react";
import { Button } from "./ui/button";
import { useState, useEffect } from "react";

const teamMembers = [
  {
    name: "Sanjai J",
    //role: "Frontend Developer",
    image: "https://github.com/sxnjai23.png", // ← replace with your github username
    github: "https://github.com/sxnjai23",
    linkedin: "https://linkedin.com/in/sanjai",
    instagram: "https://instagram.com/sxnjii_23",
  },
  {
    name: "Karthikeyan S",
   // role: "Backend Developer",
    image: "https://github.com/karthikeyan9042.png",
    github: "https://github.com/karthikeyan9042",
    linkedin: "https://linkedin.com/in/friend1",
    instagram: "https://instagram.com/friend1",
  },
  {
    name: "Ragul J",
    //role: "AI/ML Engineer",
    image: "https://github.com/Ragul3008.png",
    github: "https://github.com/Ragul3008",
    linkedin: "https://linkedin.com/in/friend2",
    instagram: "https://instagram.com/friend2",
  },

  {
    name: "Kabilan RK",
    //role: "AI/ML Engineer",
    image: "https://github.com/friend2.png",
    github: "https://github.com/kabilan-ML-Dev",
    linkedin: "https://linkedin.com/in/kabilan-ML-Dev",
    instagram: "https://instagram.com/friend2",
  },
];

export function Developer() {
  const [shuffled, setShuffled] = useState(teamMembers);

  useEffect(() => {
    setShuffled([...teamMembers].sort(() => Math.random() - 0.5));
  }, []);

  const technologies = [
    "React",
    "TypeScript",
    "Tailwind CSS",
    "TensorFlow",
    "Machine Learning",
    "Computer Vision",
  ];

  const links = [
    {
      icon: Github,
      label: "GitHub",
      url: "https://github.com",
      color: "text-gray-700 hover:text-gray-900",
    },
    {
      icon: Linkedin,
      label: "LinkedIn",
      url: "https://linkedin.com",
      color: "text-blue-600 hover:text-blue-700",
    },
    {
      icon: Mail,
      label: "Email",
      url: "mailto:dev@agroguard.ai",
      color: "text-green-600 hover:text-green-700",
    },
    {
      icon: Globe,
      label: "Website",
      url: "https://agroguard.ai",
      color: "text-purple-600 hover:text-purple-700",
    },
  ];

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="max-w-md mx-auto p-6 space-y-6 pb-8">
        {/* Profile Section */}
        <div className="bg-white rounded-xl shadow-md p-6 text-center">
          <img
            src="/logo.png"
            alt="AgroGuard AI Logo"
            className="w-24 h-24 rounded-full object-cover shadow-lg mx-auto mb-4 bg-white p-1"
          />
          <h1 className="text-2xl font-bold text-gray-800 mb-1">
            AgroGuard Development Team
          </h1>
          <p className="text-green-600 font-medium mb-2">AI & Agriculture Specialists</p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Passionate about leveraging technology to solve real-world agricultural challenges
            and empower farmers globally.
          </p>
        </div>

        {/* About Developer */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-3 flex items-center gap-2">
            <Heart className="w-5 h-5 text-red-500" />
            About the Team
          </h2>
          <p className="text-gray-700 leading-relaxed mb-3">
            We are a dedicated team of developers, data scientists, and agricultural experts
            committed to making crop disease detection accessible to everyone. Our expertise
            spans artificial intelligence, computer vision, and sustainable agriculture.
          </p>
          <p className="text-gray-700 leading-relaxed">
            AgroGuard.ai was born from our vision to bridge the gap between advanced
            technology and traditional farming, helping farmers protect their crops and
            improve yields through early disease detection.
          </p>
        </div>
        {/* Team Members */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-2">👨‍💻 Meet the Team</h2>
          <p className="text-xs text-gray-400 mb-4">✨ Order changes every visit!</p>
          <div className="space-y-4">
            {shuffled.map((member, index) => (
              <div key={index} className="flex items-center gap-4 p-3 border border-gray-100 rounded-xl">
                <img
                  src={member.image}
                  alt={member.name}
                  className="w-14 h-14 rounded-full object-cover border-2 border-green-500"
                />
                <div className="flex-1">
                  <h3 className="font-bold text-gray-800">{member.name}</h3>
                  <p className="text-sm text-green-600">{member.role}</p>
                  <div className="flex gap-3 mt-1">
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

        {/* Technologies Used */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Technologies Used</h2>
          <div className="flex flex-wrap gap-2">
            {technologies.map((tech, index) => (
              <span
                key={index}
                className="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Contact Links */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Connect With Us</h2>
          <div className="grid grid-cols-2 gap-3">
            {links.map((link, index) => {
              const Icon = link.icon;
              return (
                <a
                  key={index}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all"
                >
                  <Icon className={`w-5 h-5 ${link.color}`} />
                  <span className="text-sm font-medium text-gray-700">
                    {link.label}
                  </span>
                </a>
              );
            })}
          </div>
        </div>

        {/* Project Info */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-3">Project Information</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">Version</span>
              <span className="font-semibold text-gray-800">1.0.0</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">Release Date</span>
              <span className="font-semibold text-gray-800">February 2026</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">License</span>
              <span className="font-semibold text-gray-800">MIT</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-600">Platform</span>
              <span className="font-semibold text-gray-800">Web & Mobile</span>
            </div>
          </div>
        </div>

        {/* Contribution */}
        <div className="bg-gradient-to-r from-green-100 to-emerald-100 rounded-xl p-6 border border-green-200">
          <h2 className="text-lg font-bold text-green-800 mb-2">Want to Contribute?</h2>
          <p className="text-sm text-green-700 mb-4">
            We welcome contributions from developers and agricultural experts. Help us make
            AgroGuard.ai even better!
          </p>
          <Button className="w-full bg-green-600 hover:bg-green-700 text-white">
            <Github className="w-4 h-4 mr-2" />
            View on GitHub
          </Button>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-600">
          <p>Built with 💚 for farmers worldwide</p>
          <p className="mt-1">© 2026 AgroGuard.ai. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
