import { useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { ArrowLeft } from "lucide-react";
import Lottie from "lottie-react";
import loginAnimation from '../../imports/Login.json';

export default function Login() {
  const { role } = useParams<{ role: 'applicant' | 'recruiter' }>();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (isSignUp) {
      // Registration
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }

      // Check if user already exists
      const users = JSON.parse(localStorage.getItem('users') || '[]');
      const existingUser = users.find((u: any) => u.email === email);

      if (existingUser) {
        setError('An account with this email already exists');
        return;
      }

      // Create new user
      const newUser = {
        id: Math.random().toString(36).substring(7),
        email,
        password,
        name,
        role,
        createdAt: new Date().toISOString(),
      };

      users.push(newUser);
      localStorage.setItem('users', JSON.stringify(users));

      // Auto login after registration
      if (role) {
        await login(email, password, role);
        navigate(role === 'recruiter' ? '/recruiter/home' : '/applicant/dashboard');
      }
    } else {
      // Sign in
      const users = JSON.parse(localStorage.getItem('users') || '[]');
      const user = users.find((u: any) => u.email === email && u.password === password && u.role === role);

      if (!user) {
        setError('Invalid email or password');
        return;
      }

      if (role) {
        await login(email, password, role);
        navigate(role === 'recruiter' ? '/recruiter/home' : '/applicant/dashboard');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 p-4 relative overflow-hidden">
      <div className="absolute top-20 left-20 w-64 h-64 bg-blue-400 rounded-full opacity-30"></div>
      <div className="absolute bottom-32 right-32 w-96 h-96 bg-blue-800 rounded-full opacity-20"></div>
      <div className="absolute top-1/2 left-10 w-40 h-40 bg-blue-300 rounded-full opacity-25"></div>

      <div className="w-full max-w-5xl flex items-center justify-between gap-12 relative z-10">
        <div className="flex-1 hidden md:flex items-center justify-center">
          <div className="w-full max-w-lg">
            <Lottie
              animationData={loginAnimation}
              loop={true}
              autoplay={true}
              style={{ width: '100%', height: 'auto' }}
            />
          </div>
        </div>

        <Card className="w-full max-w-md bg-white shadow-2xl">
          <CardHeader>
            <Button
              variant="ghost"
              className="w-fit mb-4 -ml-2"
              onClick={() => navigate('/')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <CardTitle className="text-2xl">
              {isSignUp ? 'Create Account' : (role === 'recruiter' ? 'Recruiter Login' : 'Applicant Login')}
            </CardTitle>
            <CardDescription>
              {isSignUp ? 'Register as a new user' : 'Enter your credentials to continue'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignUp && (
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {isSignUp && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">
                {isSignUp ? 'Sign Up' : 'Sign In'}
              </Button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsSignUp(!isSignUp);
                    setError('');
                    setEmail('');
                    setPassword('');
                    setConfirmPassword('');
                    setName('');
                  }}
                  className="text-sm text-blue-600 hover:underline"
                >
                  {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
