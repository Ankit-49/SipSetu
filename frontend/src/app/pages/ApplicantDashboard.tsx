import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { User, LogOut, FileText, Upload, Briefcase, GraduationCap } from "lucide-react";

interface Resume {
  id: string;
  name: string;
  type: 'template' | 'uploaded';
  template?: string;
  file?: File;
  createdAt: string;
}

const templates = [
  {
    id: 'professional',
    name: 'Professional',
    description: 'Clean and modern design for corporate positions',
    icon: Briefcase,
    color: 'blue',
  },
  {
    id: 'creative',
    name: 'Creative',
    description: 'Bold design for creative industries',
    icon: FileText,
    color: 'purple',
  },
  {
    id: 'academic',
    name: 'Academic',
    description: 'Traditional format for academic positions',
    icon: GraduationCap,
    color: 'green',
  },
];

export default function ApplicantDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [resumes, setResumes] = useState<Resume[]>(() => {
    const stored = localStorage.getItem('resumes');
    return stored ? JSON.parse(stored) : [];
  });

  useEffect(() => {
    if (!user || user.role !== 'applicant') {
      navigate('/');
    }
  }, [user, navigate]);

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      const newResume: Resume = {
        id: Math.random().toString(36).substring(7),
        name: `${template.name} Resume`,
        type: 'template',
        template: templateId,
        createdAt: new Date().toISOString(),
      };
      const updatedResumes = [...resumes, newResume];
      setResumes(updatedResumes);
      localStorage.setItem('resumes', JSON.stringify(updatedResumes));
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const newResume: Resume = {
        id: Math.random().toString(36).substring(7),
        name: file.name,
        type: 'uploaded',
        createdAt: new Date().toISOString(),
      };
      const updatedResumes = [...resumes, newResume];
      setResumes(updatedResumes);
      localStorage.setItem('resumes', JSON.stringify(updatedResumes));
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-blue-50">
      <nav className="bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3 text-white">
            <User className="w-6 h-6" />
            <div>
              
              
            </div>
          </div>
          <Button variant="secondary" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl mb-2">Welcome back!</h1>
          <p className="text-gray-600">Manage your resumes and find opportunities</p>
        </div>

        <Tabs defaultValue="create" className="space-y-6">
          <TabsList>
            <TabsTrigger value="create">Create Resume</TabsTrigger>
            <TabsTrigger value="my-resumes">My Resumes</TabsTrigger>
          </TabsList>

          <TabsContent value="create" className="space-y-6">
            <div>
              <h2 className="text-xl mb-4">Choose a Template</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {templates.map((template) => {
                  const Icon = template.icon;
                  return (
                    <Card
                      key={template.id}
                      className="cursor-pointer hover:shadow-xl transition-all transform hover:scale-105 border-blue-200"
                      onClick={() => handleTemplateSelect(template.id)}
                    >
                      <CardHeader>
                        <div className="w-14 h-14 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
                          <Icon className="w-7 h-7 text-blue-600" />
                        </div>
                        <CardTitle>{template.name}</CardTitle>
                        <CardDescription>{template.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button className="w-full bg-blue-600 hover:bg-blue-700">Use Template</Button>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            <div>
              <h2 className="text-xl mb-4">Upload Your Resume</h2>
              <Card>
                <CardContent className="pt-6">
                  <div className="border-2 border-dashed rounded-lg p-12 text-center">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="mb-2">Upload your existing resume</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Supports PDF, DOC, DOCX files
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <Button onClick={() => fileInputRef.current?.click()}>
                      Choose File
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="my-resumes">
            {resumes.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg mb-2">No resumes yet</h3>
                  <p className="text-gray-600 mb-4">Create your first resume to get started</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {resumes.map((resume) => (
                  <Card key={resume.id}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg">{resume.name}</CardTitle>
                          <CardDescription>
                            Created on {new Date(resume.createdAt).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <Badge variant={resume.type === 'template' ? 'default' : 'secondary'}>
                          {resume.type === 'template' ? 'Template' : 'Uploaded'}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-2">
                        <Button variant="outline" className="flex-1">View</Button>
                        <Button variant="outline" className="flex-1">Edit</Button>
                        <Button variant="outline" className="flex-1">Download</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
