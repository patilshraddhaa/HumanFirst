import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../shared/utils";
const badgeVariants = cva("inline-flex items-center rounded-none border border-foreground px-2 py-1 font-mono text-[0.65rem] font-medium uppercase tracking-[0.08em]", { variants: { variant: { default: "bg-primary text-primary-foreground", secondary: "bg-secondary text-secondary-foreground", outline: "text-foreground", human: "bg-[#c8d8c8] text-foreground", ai: "bg-[#f2c6b7] text-foreground" } }, defaultVariants: { variant: "default" } });
function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) { return <div className={cn(badgeVariants({ variant }), className)} {...props} />; }
export { Badge, badgeVariants };
