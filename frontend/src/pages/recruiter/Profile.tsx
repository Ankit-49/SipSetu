import { useState, useEffect } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Camera, MapPin, Phone, Mail, User, Building, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/app/context/AuthContext";

export default function RecruiterProfile() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    location: "",
    company: "",
    role: "", // This is the job title in the UI
    profileImage: "",
  });

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchProfile = async () => {
      try {
        const response = await api.get(`/profile/${user.id}`);
        const fullName = response.data.name || "";
        const [firstName, ...lastNameParts] = fullName.split(" ");

        setProfile({
          firstName: firstName || "",
          lastName: lastNameParts.join(" ") || "",
          email: response.data.email || "",
          phone: response.data.phone || "",
          location: response.data.location || "",
          company: response.data.company || "",
          role: response.data.job_title || "",
          profileImage: response.data.profile_image || "",
        });
      } catch (error) {
        console.error("Error fetching profile:", error);
        toast({
          title: "Error",
          description: "Failed to load profile data.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        toast({ title: "Error", description: "Image must be less than 2MB", variant: "destructive" });
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfile(prev => ({ ...prev, profileImage: reader.result as string }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async () => {
    if (!user) return;

    setSaving(true);
    try {
      await api.put(`/profile/${user.id}`, {
        name: `${profile.firstName} ${profile.lastName}`.trim(),
        email: profile.email,
        phone: profile.phone,
        location: profile.location,
        company: profile.company,
        job_title: profile.role,
        profile_image: profile.profileImage,
      });

      localStorage.setItem("user_name", `${profile.firstName} ${profile.lastName}`.trim());
      if (profile.profileImage) {
        localStorage.setItem("profile_image", profile.profileImage);
        window.dispatchEvent(new Event("storage")); // Trigger layout update
      }

      toast({
        title: "Success",
        description: "Profile updated successfully.",
      });
    } catch (error) {
      console.error("Error saving profile:", error);
      toast({
        title: "Error",
        description: "Failed to save profile changes.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#F97316]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Recruiter Profile</h1>
        <p className="text-slate-500 mt-1">Manage your account and company details.</p>
      </div>

      <Card>
        <CardContent className="p-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            <div className="flex flex-col items-center space-y-4">
              <div className="relative group">
                <input 
                  type="file" 
                  id="profile-upload" 
                  className="hidden" 
                  accept="image/*"
                  onChange={handleImageChange}
                />
                <label htmlFor="profile-upload" className="cursor-pointer block">
                  <Avatar className="h-32 w-32 border-4 border-white shadow-md">
                    <AvatarImage src={profile.profileImage} className="object-cover" />
                    <AvatarFallback className="bg-[#F97316] text-white text-3xl font-bold">
                      {profile.firstName[0]}{profile.lastName[0]}
                    </AvatarFallback>
                  </Avatar>
                  <div className="absolute bottom-2 right-2 h-8 w-8 bg-[#1E3A5F] text-white rounded-full flex items-center justify-center shadow-lg hover:bg-[#1E3A5F]/90 transition-colors pointer-events-none">
                    <Camera className="h-4 w-4" />
                  </div>
                </label>
              </div>
              <p className="text-sm font-medium text-slate-500">JPG, GIF or PNG. Max size of 2MB.</p>
            </div>

            <Separator orientation="vertical" className="hidden md:block h-auto" />

            <div className="flex-1 space-y-8 w-full">
              {/* Personal Details */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-100 pb-2 mb-4">Personal Details</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="firstName" 
                        value={profile.firstName} 
                        onChange={(e) => setProfile({ ...profile, firstName: e.target.value })}
                        className="pl-9" 
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="lastName" 
                        value={profile.lastName} 
                        onChange={(e) => setProfile({ ...profile, lastName: e.target.value })}
                        className="pl-9" 
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Work Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="email" 
                        type="email" 
                        value={profile.email} 
                        readOnly
                        className="pl-9 cursor-not-allowed bg-slate-50" 
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="phone" 
                        type="tel" 
                        value={profile.phone} 
                        onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                        className="pl-9" 
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Company Details */}
              <div className="space-y-6 pt-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-100 pb-2 mb-4">Company Details</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="company">Company Name</Label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="company" 
                        value={profile.company} 
                        onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                        className="pl-9" 
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Your Role / Title</Label>
                    <Input 
                      id="role" 
                      value={profile.role} 
                      onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="location">Office Location</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input 
                        id="location" 
                        value={profile.location} 
                        onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                        className="pl-9" 
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6 mt-6 border-t border-slate-100">
                <Button variant="outline">Cancel</Button>
                <Button 
                  className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Profile"
                  )}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
