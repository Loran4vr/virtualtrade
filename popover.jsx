import * as React from "react";
import { cn } from "../../lib/utils";

const Popover = ({ children, open, onOpenChange, ...props }) => {
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
    <PopoverContext.Provider value={{ open: isOpen, onOpenChange: handleOpenChange }}>
      {children}
    </PopoverContext.Provider>
  );
};

const PopoverContext = React.createContext({});

const usePopoverContext = () => {
  const context = React.useContext(PopoverContext);
  if (!context) {
    throw new Error("Popover components must be used within a Popover");
  }
  return context;
};

const PopoverTrigger = ({ children, asChild = false, ...props }) => {
  const { onOpenChange, open } = usePopoverContext();
  const Comp = asChild ? React.Fragment : "button";
  
  return (
    <Comp onClick={() => onOpenChange(!open)} {...props}>
      {children}
    </Comp>
  );
};

const PopoverContent = ({ className, align = "center", children, ...props }) => {
  const { open } = usePopoverContext();
  
  if (!open) return null;
  
  return (
    <div
      className={cn(
        "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none",
        {
          "ml-auto": align === "end",
          "mr-auto": align === "start",
          "mx-auto": align === "center",
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export { Popover, PopoverTrigger, PopoverContent };

