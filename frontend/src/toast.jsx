import * as React from "react";
import { cn } from "../../lib/utils";

const ToastProvider = ({ children, ...props }) => {
  return <div {...props}>{children}</div>;
};

const ToastViewport = ({ className, ...props }) => (
  <div
    className={cn(
      "fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]",
      className
    )}
    {...props}
  />
);
ToastViewport.displayName = "ToastViewport";

const Toast = ({ className, variant, ...props }) => {
  return (
    <div
      className={cn(
        "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all",
        {
          "bg-background text-foreground": variant === "default",
          "bg-destructive text-destructive-foreground": variant === "destructive",
        },
        className
      )}
      {...props}
    />
  );
};
Toast.displayName = "Toast";

const ToastTitle = ({ className, ...props }) => (
  <div
    className={cn("text-sm font-semibold", className)}
    {...props}
  />
);
ToastTitle.displayName = "ToastTitle";

const ToastDescription = ({ className, ...props }) => (
  <div
    className={cn("text-sm opacity-90", className)}
    {...props}
  />
);
ToastDescription.displayName = "ToastDescription";

const ToastClose = ({ className, ...props }) => (
  <button
    className={cn(
      "absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100",
      className
    )}
    {...props}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4"
    >
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  </button>
);
ToastClose.displayName = "ToastClose";

const Toaster = () => {
  const [toasts, setToasts] = React.useState([]);

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            {action}
            <ToastClose onClick={() => setToasts((t) => t.filter((toast) => toast.id !== id))} />
          </Toast>
        );
      })}
      <ToastViewport />
    </ToastProvider>
  );
};

const useToast = () => {
  const [toasts, setToasts] = React.useState([]);

  const toast = React.useCallback(
    ({ title, description, variant, duration = 5000 }) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prevToasts) => [
        ...prevToasts,
        { id, title, description, variant, duration },
      ]);

      if (duration) {
        setTimeout(() => {
          setToasts((prevToasts) =>
            prevToasts.filter((toast) => toast.id !== id)
          );
        }, duration);
      }

      return id;
    },
    []
  );

  const dismiss = React.useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);

  return { toast, dismiss, toasts };
};

export { Toaster, useToast };

