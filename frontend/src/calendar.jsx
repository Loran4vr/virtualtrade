import * as React from "react";
import { cn } from "./utils";

const Calendar = ({ className, ...props }) => {
  return (
    <div className={cn("p-3", className)}>
      <div className="flex justify-between mb-2">
        <button className="p-1">&lt;</button>
        <div>June 2025</div>
        <button className="p-1">&gt;</button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        <div className="text-center text-sm">Su</div>
        <div className="text-center text-sm">Mo</div>
        <div className="text-center text-sm">Tu</div>
        <div className="text-center text-sm">We</div>
        <div className="text-center text-sm">Th</div>
        <div className="text-center text-sm">Fr</div>
        <div className="text-center text-sm">Sa</div>
        
        {/* Empty cells for days before the 1st */}
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        
        {/* Days of the month */}
        {Array.from({ length: 30 }, (_, i) => (
          <button
            key={i}
            className={cn(
              "h-9 w-9 rounded-md p-0 font-normal aria-selected:opacity-100",
              i === 5 ? "bg-primary text-primary-foreground" : "hover:bg-accent"
            )}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
};
Calendar.displayName = "Calendar";

export { Calendar };

