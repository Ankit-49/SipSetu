import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Camera, MapPin, Phone, Mail, User, Building } from "lucide-react";

export default function RecruiterProfile() {
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
                <Avatar className="h-32 w-32 border-4 border-white shadow-md">
                  <AvatarImage src="" />
                  <AvatarFallback className="bg-[#F97316] text-white text-3xl font-bold">RM</AvatarFallback>
                </Avatar>
                <button className="absolute bottom-2 right-2 h-8 w-8 bg-[#1E3A5F] text-white rounded-full flex items-center justify-center shadow-lg hover:bg-[#1E3A5F]/90 transition-colors">
                  <Camera className="h-4 w-4" />
                </button>
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
                      <Input id="firstName" defaultValue="Rahul" className="pl-9" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="lastName" defaultValue="Mehta" className="pl-9" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Work Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="email" type="email" defaultValue="rahul.mehta@techcorp.in" className="pl-9" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="phone" type="tel" defaultValue="+91 98765 12345" className="pl-9" />
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
                      <Input id="company" defaultValue="TechCorp Solutions" className="pl-9" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Your Role / Title</Label>
                    <Input id="role" defaultValue="Senior HR Manager" />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="location">Office Location</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input id="location" defaultValue="Bangalore, Karnataka, India" className="pl-9" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6 mt-6 border-t border-slate-100">
                <Button variant="outline">Cancel</Button>
                <Button className="bg-[#1E3A5F] hover:bg-[#1E3A5F]/90">Save Profile</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
