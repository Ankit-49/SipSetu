// Thin shim that re-exports Sonner's toast API in the shadcn shape used
// throughout this codebase: { toast } = useToast(); toast({ title, description, variant })
// Sonner renders at the bottom-right by default, which matches the requirement
// of a "UI component on the bottom of screen" instead of an alert dialog.
import { toast as sonnerToast } from "sonner";

type ToastVariant = "default" | "destructive";

interface ToastInput {
  title?: React.ReactNode;
  description?: React.ReactNode;
  variant?: ToastVariant;
  duration?: number;
}

function nodeToString(node: React.ReactNode): string | undefined {
  if (node == null || node === false) return undefined;
  if (typeof node === "string" || typeof node === "number") return String(node);
  return undefined;
}

function toToast(props: ToastInput) {
  const { title, description, variant, duration } = props;
  const titleStr = nodeToString(title);
  const descStr = nodeToString(description);

  const options = {
    duration,
    description: descStr,
  };

  if (variant === "destructive") {
    return sonnerToast.error(titleStr ?? "Something went wrong", options);
  }
  return sonnerToast.success(titleStr ?? "Success", options);
}

function useToast() {
  return {
    toast: toToast,
    dismiss: (id?: string | number) => sonnerToast.dismiss(id),
    toasts: [],
  };
}

export { useToast, toToast as toast };
