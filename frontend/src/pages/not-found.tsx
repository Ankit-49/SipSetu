import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-react";
import { SipSetuLogo } from "@/components/SipSetuLogo";
import { VisualBackground } from "@/components/VisualBackground";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 selection:bg-[#F97316] selection:text-white">
      <VisualBackground />

      <div className="relative z-10 text-center max-w-lg">
        <div className="mb-8">
          <SipSetuLogo className="text-4xl font-black tracking-tighter text-white/90" />
        </div>

        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-white/10 backdrop-blur-sm mb-8">
          <span className="text-5xl font-black text-white">404</span>
        </div>

        <h1 className="text-3xl font-bold text-white mb-3">Page not found</h1>
        <p className="text-blue-100 text-lg mb-8 max-w-sm mx-auto leading-relaxed">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/">
            <Button className="h-12 px-8 bg-white text-[#1E3A5F] hover:bg-white/90 font-bold shadow-lg shadow-black/20">
              <Home className="mr-2 h-4 w-4" /> Go Home
            </Button>
          </Link>
          <Button
            variant="outline"
            className="h-12 px-8 border-white/30 text-white bg-white/5 hover:bg-white/10 hover:text-white"
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}
