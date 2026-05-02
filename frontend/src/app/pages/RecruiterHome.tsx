import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { motion, AnimatePresence } from "motion/react";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  UserCircle,
  LogOut,
  FileText,
  TrendingUp,
  UserCheck,
  Target,
  Menu
} from "lucide-react";

interface Candidate {
  id: string;
  name: string;
  title: string;
  location: string;
  experience: string;
  skills: string[];
  matchScore: number;
  status: 'Applied' | 'In Review' | 'Shortlisted' | 'Rejected';
}

export default function RecruiterHome() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userName, setUserName] = useState('User');
  const [sidebarVisible, setSidebarVisible] = useState(false);

  useEffect(() => {
    if (!user || user.role !== 'recruiter') {
      navigate('/');
    } else {
      // Get user's name from localStorage
      const users = JSON.parse(localStorage.getItem('users') || '[]');
      const currentUser = users.find((u: any) => u.email === user.email);
      if (currentUser && currentUser.name) {
        setUserName(currentUser.name);
      }
    }
  }, [user, navigate]);

  // Mock data
  const stats = {
    activePostings: 5,
    totalApplicants: 143,
    shortlisted: 28,
    hiresThisMonth: 3
  };

  const topMatches: Candidate[] = [
    {
      id: '1',
      name: 'Priya Sharma',
      title: 'Frontend Developer',
      location: 'Mumbai',
      experience: '3 years exp.',
      skills: ['React', 'TypeScript', 'CSS', 'Git'],
      matchScore: 94,
      status: 'Shortlisted'
    },
    {
      id: '2',
      name: 'Arjun Nair',
      title: 'Full Stack Developer',
      location: 'Bangalore',
      experience: '4 years exp.',
      skills: ['Node.js', 'React', 'PostgreSQL', 'Docker'],
      matchScore: 88,
      status: 'In Review'
    },
    {
      id: '3',
      name: 'Sneha Patel',
      title: 'UI Developer',
      location: 'Pune',
      experience: '2 years exp.',
      skills: ['CSS', 'Figma', 'HTML', 'JavaScript'],
      matchScore: 84,
      status: 'Applied'
    }
  ];

  const activeJobs = [
    { id: '1', title: 'Frontend Developer', applicants: 47, daysAgo: 3 },
    { id: '2', title: 'Backend Engineer', applicants: 31, daysAgo: 5 },
    { id: '3', title: 'DevOps Engineer', applicants: 22, daysAgo: 7 }
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex relative">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarVisible && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/20 z-40"
              onClick={() => setSidebarVisible(false)}
            />

            {/* Sidebar Panel */}
            <motion.aside
              initial={{ x: -256 }}
              animate={{ x: 0 }}
              exit={{ x: -256 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-blue-600 to-blue-800 text-white flex flex-col shadow-2xl z-50"
            >
              <div className="p-6 border-b border-blue-500/30">
                <h1 className="text-2xl font-semibold">SipSetu</h1>
              </div>

              <nav className="flex-1 px-4 py-6">
                <button
                  onClick={() => {
                    setActiveTab('dashboard');
                    setSidebarVisible(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all ${
                    activeTab === 'dashboard'
                      ? 'bg-white text-blue-600 shadow-lg'
                      : 'hover:bg-blue-500/30 text-white'
                  }`}
                >
                  <LayoutDashboard className="w-5 h-5" />
                  Dashboard
                </button>
                <button
                  onClick={() => {
                    navigate('/recruiter/post-job');
                    setSidebarVisible(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all hover:bg-blue-500/30 text-white"
                >
                  <Briefcase className="w-5 h-5" />
                  Post Job
                </button>
                <button
                  onClick={() => {
                    navigate('/recruiter/candidates');
                    setSidebarVisible(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all hover:bg-blue-500/30 text-white"
                >
                  <Users className="w-5 h-5" />
                  Candidates
                </button>
                <button
                  onClick={() => {
                    navigate('/recruiter/profile');
                    setSidebarVisible(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all ${
                    activeTab === 'profile'
                      ? 'bg-white text-blue-600 shadow-lg'
                      : 'hover:bg-blue-500/30 text-white'
                  }`}
                >
                  <UserCircle className="w-5 h-5" />
                  Profile
                </button>
              </nav>

              <div className="p-4 border-t border-blue-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-white text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                    {userName.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate font-medium">{userName}</p>
                    <p className="text-xs text-blue-200">HR Manager</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  className="w-full text-white hover:bg-blue-500/30"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Menu Button - Always visible */}
      <button
        onClick={() => setSidebarVisible(true)}
        className="fixed top-4 left-4 z-30 w-10 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center justify-center shadow-lg transition-colors"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Main Content */}
      <main className="flex-1 overflow-auto w-full">
        <div className="p-8 pl-20">
          {/* Header */}
          <div className="mb-8 flex justify-between items-center">
            <div>
              <h2 className="text-3xl mb-1">Good morning, {userName.split(' ')[0]}! 👋</h2>
              <p className="text-gray-500">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <Button className="bg-orange-500 hover:bg-orange-600">
              + Post New Job
            </Button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">Active Postings</p>
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>
                <p className="text-3xl">{stats.activePostings}</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">Total Applicants</p>
                  <Users className="w-5 h-5 text-purple-500" />
                </div>
                <p className="text-3xl">{stats.totalApplicants}</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">Shortlisted</p>
                  <Target className="w-5 h-5 text-orange-500" />
                </div>
                <p className="text-3xl text-orange-500">{stats.shortlisted}</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">Hires This Month</p>
                  <UserCheck className="w-5 h-5 text-green-500" />
                </div>
                <p className="text-3xl text-green-500">{stats.hiresThisMonth}</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Top Matches */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Top Matches (AI Ranked)</CardTitle>
                <button className="text-sm text-blue-600 hover:underline">View All →</button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topMatches.map((candidate, index) => (
                    <div key={candidate.id} className="flex items-start gap-4 pb-4 border-b last:border-0">
                      <div className="w-10 h-10 bg-slate-700 text-white rounded-full flex items-center justify-center flex-shrink-0">
                        {candidate.name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <div>
                            <h4 className="font-semibold">{candidate.name}</h4>
                            <p className="text-sm text-gray-600">{candidate.title}</p>
                          </div>
                          <Badge
                            className={
                              candidate.status === 'Shortlisted' ? 'bg-green-100 text-green-700' :
                              candidate.status === 'In Review' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }
                          >
                            {candidate.status}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {candidate.skills.slice(0, 4).map((skill) => (
                            <span key={skill} className="text-xs bg-gray-100 px-2 py-1 rounded">
                              {skill}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="font-semibold text-green-600">{candidate.matchScore}% Match</span>
                          <Button variant="outline" size="sm">Resume</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Active Job Postings */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Active Job Postings</CardTitle>
                <button className="text-sm text-blue-600 hover:underline">View all postings</button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activeJobs.map((job) => (
                    <div key={job.id} className="p-4 border rounded-lg hover:border-blue-300 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">{job.title}</h4>
                        <Badge>Active</Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {job.applicants} Applicants
                        </span>
                        <span>{job.daysAgo} days ago</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
