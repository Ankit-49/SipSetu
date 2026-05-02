import { useState } from "react";
import { useNavigate } from "react-router";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Search, FileText, Mail, ChevronDown } from "lucide-react";

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

export default function RankedCandidates() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPosting, setFilterPosting] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Mock candidates data
  const [candidates, setCandidates] = useState<Candidate[]>([
    {
      id: '1',
      name: 'Priya Sharma',
      title: 'Frontend Developer',
      location: 'Mumbai',
      experience: '3 years exp.',
      skills: ['React', 'TypeScript', 'CSS', 'Git'],
      matchScore: 92,
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
    },
    {
      id: '4',
      name: 'Vikram Singh',
      title: 'Frontend Developer',
      location: 'Delhi',
      experience: '2 years exp.',
      skills: ['React', 'JavaScript', 'Webpack'],
      matchScore: 79,
      status: 'Applied'
    },
    {
      id: '5',
      name: 'Meera Krishnan',
      title: 'Backend Engineer',
      location: 'Chennai',
      experience: '3 years exp.',
      skills: ['Node.js', 'Express', 'MongoDB'],
      matchScore: 76,
      status: 'Rejected'
    },
    {
      id: '6',
      name: 'Rohit Gupta',
      title: 'Full Stack Developer',
      location: 'Hyderabad',
      experience: '2 years exp.',
      skills: ['React', 'Node.js', 'MySQL'],
      matchScore: 73,
      status: 'Applied'
    }
  ]);

  const updateCandidateStatus = (candidateId: string, newStatus: Candidate['status']) => {
    setCandidates(candidates.map(c =>
      c.id === candidateId ? { ...c, status: newStatus } : c
    ));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Shortlisted': return 'bg-green-100 text-green-700';
      case 'In Review': return 'bg-blue-100 text-blue-700';
      case 'Applied': return 'bg-gray-100 text-gray-700';
      case 'Rejected': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getMatchColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-orange-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/recruiter/home')} className="mb-6">
          ← Back to Dashboard
        </Button>

        <div className="mb-8">
          <h1 className="text-4xl mb-2">Ranked Candidates</h1>
          <p className="text-gray-600">
            Applicants automatically scored and ranked against your job requirements.
          </p>
        </div>

        {/* Search and Filters */}
        <Card className="p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <Input
                placeholder="Search candidates or skills..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Select value={filterPosting} onValueChange={setFilterPosting}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="All Postings" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Postings</SelectItem>
                <SelectItem value="frontend">Frontend Developer</SelectItem>
                <SelectItem value="backend">Backend Engineer</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Any Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any Status</SelectItem>
                <SelectItem value="applied">Applied</SelectItem>
                <SelectItem value="review">In Review</SelectItem>
                <SelectItem value="shortlisted">Shortlisted</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </Card>

        {/* Candidates List */}
        <div className="space-y-4">
          {candidates.map((candidate, index) => (
            <Card key={candidate.id} className="p-6">
              <div className="flex items-start gap-6">
                {/* Rank and Match Score */}
                <div className="flex flex-col items-center">
                  <div className="text-sm text-gray-500 mb-1">RANK #{index + 1}</div>
                  <div className={`text-3xl ${getMatchColor(candidate.matchScore)}`}>
                    {candidate.matchScore}%
                  </div>
                  <div className="text-xs text-gray-500">MATCH</div>
                </div>

                {/* Avatar */}
                <div className="w-12 h-12 bg-slate-700 text-white rounded-full flex items-center justify-center flex-shrink-0">
                  {candidate.name.substring(0, 2).toUpperCase()}
                </div>

                {/* Candidate Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div>
                      <h3 className="text-lg font-semibold mb-1">{candidate.name}</h3>
                      <p className="text-gray-600 text-sm mb-1">@ {candidate.title}</p>
                      <p className="text-gray-500 text-sm">
                        📍 {candidate.location} • {candidate.experience}
                      </p>
                    </div>
                    <Badge className={getStatusColor(candidate.status)}>
                      {candidate.status}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {candidate.skills.map((skill) => (
                      <span
                        key={skill}
                        className="text-sm bg-gray-100 px-3 py-1 rounded-full"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-3">
                    <Button variant="ghost" size="sm">
                      <Mail className="w-4 h-4 mr-2" />
                    </Button>
                    <Button variant="default" size="sm" className="bg-slate-800 hover:bg-slate-700">
                      <FileText className="w-4 h-4 mr-2" />
                      View Resume
                    </Button>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm">
                          Status <ChevronDown className="w-4 h-4 ml-2" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-48">
                        <DropdownMenuItem onClick={() => updateCandidateStatus(candidate.id, 'Applied')}>
                          Mark as Applied
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => updateCandidateStatus(candidate.id, 'In Review')}
                          className="text-blue-600"
                        >
                          Move to Review
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => updateCandidateStatus(candidate.id, 'Shortlisted')}
                          className="text-green-600"
                        >
                          Shortlist
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => updateCandidateStatus(candidate.id, 'Rejected')}
                          className="text-red-600"
                        >
                          Reject
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
