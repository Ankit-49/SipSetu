import { motion } from "framer-motion";

export const VisualBackground = () => {
  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Primary Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700" />
      
      {/* Animated background circles from luja2 */}
      <motion.div
        className="absolute top-20 left-20 w-64 h-64 bg-blue-400 rounded-full opacity-30"
        animate={{
          scale: [1, 1.2, 1],
          x: [0, 50, 0],
          y: [0, 30, 0],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute bottom-32 right-32 w-96 h-96 bg-blue-800 rounded-full opacity-20"
        animate={{
          scale: [1, 1.1, 1],
          x: [0, -30, 0],
          y: [0, -50, 0],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1
        }}
      />
      <motion.div
        className="absolute top-1/2 left-10 w-40 h-40 bg-blue-300 rounded-full opacity-25"
        animate={{
          x: [0, 20, 0],
          y: [0, -20, 0],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2
        }}
      />
      
      {/* Subtle overlay for depth */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.1)_100%)]" />
    </div>
  );
};
