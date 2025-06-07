import * as React from "react";
import { cn } from "../../lib/utils";

const Dialog = ({ children, open, onOpenChange, ...props }) => {
  const [isOpen, setIsOpen] = React.useState(open || false);

  React.useEffect(() => {
    if (open !== undefined) {
      setIsOpen(open);
      if (onOpenChange) {
        onOpenChange(open);
      }
    }
  }, [open, onOpenChange]);

  const handleOpenChange = (value) => {
    setIsOpen(value);
    if (onOpenChange) {
      onOpenChange(value);
    }
  };

  return (
    <DialogContext.Provider value={{ open: isOpen, onOpenChange: handleOpenChange }}>
      {children}
    </DialogContext.Provider>
  );
};

const DialogContext = React.createContext({});

const useDialogContext = () => {
  const context = React.useContext(DialogContext);
  if (!context) {
    throw new Error("Dialog components must be used within a Dialog");
  }
  return context;
};

const DialogTrigger = ({ children, asChild = false, ...props }) => {
  const { onOpenChange } = useDialogContext();
  const Comp = asChild ? React.Fragment : "button";
  
  return (
    <Comp onClick={() => onOpenChange(true)} {...props}>
      {children}
    </Comp>
  );
};

const DialogContent = ({ className, children, ...props }) => {
  const { open, onOpenChange } = useDialogContext();
  
  if (!open) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="fixed inset-0 bg-black/50" 
        onClick={() => onOpenChange(false)}
      />
      <div
        className={cn(
          "fixed z-50 grid w-full max-w-lg scale-100 gap-4 bg-background p-6 opacity-100 shadow-lg border rounded-lg",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </div>
  );
};

const DialogHeader = ({ className, ...props }) => (
  <div
    className={cn(
      "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    )}
    {...props}
  />
);

const DialogFooter = ({ className, ...props }) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  />
);

const DialogTitle = ({ className, ...props }) => (
  <h3
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
);

const DialogDescription = ({ className, ...props }) => (
  <p
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
);

export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};

