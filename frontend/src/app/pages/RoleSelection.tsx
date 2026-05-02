import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Briefcase, User, Upload, Target, GraduationCap, FileText, Users, CheckCircle, HelpCircle, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { Button } from "../components/ui/button";

export default function RoleSelection() {
  const navigate = useNavigate();
  const [showHelp, setShowHelp] = useState(false);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 p-4 relative overflow-hidden">
      {/* Help Button */}
      <motion.div
        className="fixed top-6 right-6 z-50"
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 1 }}
      >
        <Button
          onClick={() => setShowHelp(!showHelp)}
          className="w-14 h-14 rounded-full bg-white text-blue-600 hover:bg-blue-50 shadow-lg"
          size="icon"
        >
          {showHelp ? <X className="w-6 h-6" /> : <HelpCircle className="w-6 h-6" />}
        </Button>
      </motion.div>

      {/* Animated background circles */}
      <motion.div
        className="absolute top-20 left-20 w-64 h-64 bg-blue-400 rounded-full opacity-30"
        animate={{
          y: [0, -20, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      ></motion.div>
      <motion.div
        className="absolute bottom-32 right-32 w-96 h-96 bg-blue-800 rounded-full opacity-20"
        animate={{
          y: [0, 20, 0],
          scale: [1, 1.05, 1],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      ></motion.div>
      <motion.div
        className="absolute top-1/2 left-10 w-40 h-40 bg-blue-300 rounded-full opacity-25"
        animate={{
          x: [0, 10, 0],
          y: [0, -10, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      ></motion.div>

      <div className="w-full max-w-5xl relative z-10">
        <div className="text-center mb-12">
          <motion.h1
            className="mb-4 text-white tracking-wide text-[96px] font-[ADLaM_Display]"
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.8,
              ease: "easeOut"
            }}
          >
            WELCOME TO
          </motion.h1>
          <motion.h2
            className="text-6xl mb-4 text-white tracking-wide font-[ADLaM_Display]"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              duration: 0.8,
              delay: 0.3,
              ease: "easeOut"
            }}
          >
            SIPSETU
          </motion.h2>
          <motion.p
            className="text-xl text-blue-100 uppercase tracking-wider"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{
              duration: 0.8,
              delay: 0.6
            }}
          >
            No Skills Left Behind
          </motion.p>
        </div>

        <motion.div
          className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.8,
            delay: 0.9
          }}
        >
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Card
              className="cursor-pointer hover:shadow-2xl transition-all duration-300 bg-white border-0"
              onClick={() => navigate('/login/applicant')}
            >
              <CardHeader className="text-center py-12">
                <div className="mx-auto w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <User className="w-10 h-10 text-blue-600" />
                </div>
                <CardTitle className="text-2xl text-gray-800">Applicant</CardTitle>
              </CardHeader>
              <CardContent className="pb-8">
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Card
              className="cursor-pointer hover:shadow-2xl transition-all duration-300 bg-white border-0"
              onClick={() => navigate('/login/recruiter')}
            >
              <CardHeader className="text-center py-12">
                <div className="mx-auto w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <Briefcase className="w-10 h-10 text-blue-600" />
                </div>
                <CardTitle className="text-2xl text-gray-800">Recruiter</CardTitle>
              </CardHeader>
              <CardContent className="pb-8">
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Help Popup */}
        <AnimatePresence>
          {showHelp && (
            <>
              {/* Backdrop */}
              <motion.div
                className="fixed inset-0 bg-black/50 z-40"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowHelp(false)}
              />

              {/* Help Card */}
              <motion.div
                className="fixed top-24 right-6 bg-white rounded-2xl shadow-2xl p-6 max-w-md z-50"
                initial={{ opacity: 0, scale: 0.8, y: -20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <h3 className="text-xl mb-4 text-gray-800">How SipSetu Works</h3>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4 text-orange-500" />
                      <h4 className="text-sm text-orange-500">For Applicants</h4>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      Upload your resume, get matched with jobs based on your skills, and discover learning resources to bridge any gaps.
                    </p>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Briefcase className="w-4 h-4 text-blue-600" />
                      <h4 className="text-sm text-blue-600">For Recruiters</h4>
                    </div>
                    <p className="text-sm text-gray-600 ml-6">
                      Post job requirements, review candidates ranked by skill match, and make data-driven hiring decisions.
                    </p>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t">
                  <p className="text-xs text-gray-500 italic">
                    "No Skills Left Behind" - We help connect talent with opportunity through intelligent skill matching.
                  </p>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
