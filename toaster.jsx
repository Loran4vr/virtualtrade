import { useToast } from "./toast";

export function Toaster() {
  const { toasts } = useToast();

  return (
    <div className="fixed top-0 right-0 z-50 flex flex-col gap-2 p-4 max-w-md">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`bg-white dark:bg-gray-800 border rounded-md shadow-lg p-4 ${
            toast.variant === "destructive" ? "border-red-500" : "border-gray-200"
          }`}
        >
          {toast.title && <div className="font-medium">{toast.title}</div>}
          {toast.description && <div className="text-sm text-gray-500 dark:text-gray-400">{toast.description}</div>}
        </div>
      ))}
    </div>
  );
}

