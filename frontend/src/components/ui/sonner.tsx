"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast !rounded-xl !border !border-slate-200/80 !bg-white !shadow-xl !shadow-slate-200/60 !text-slate-900 !px-4 !py-3 !gap-3 !items-start",
          title: "!text-sm !font-semibold !text-slate-900",
          description: "!text-xs !text-slate-500 !mt-0.5",
          success:
            "!border-l-4 !border-l-emerald-500",
          error:
            "!border-l-4 !border-l-red-500",
          warning:
            "!border-l-4 !border-l-amber-500",
          info:
            "!border-l-4 !border-l-blue-500",
          icon: "!mt-0.5",
          closeButton:
            "!bg-slate-100 !border-slate-200 !text-slate-500 hover:!bg-slate-200 !rounded-lg",
          actionButton:
            "!bg-[#1E3A5F] !text-white !rounded-lg",
          cancelButton:
            "!bg-slate-100 !text-slate-600 !rounded-lg",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
